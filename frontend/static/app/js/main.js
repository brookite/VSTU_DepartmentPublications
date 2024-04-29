const endpoint = window.location.href.split('?')[0].split('/').at(-1);
const secondaryEndpoints = ["updates"];

$.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Только если URL не внешний
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
});

function flash(text) {}

function setDepartments(facultyId) {
  $(".departmentSelect").html("");
  let container = $(".departmentSelect").get(0);
  for (let department of departments) {
    if (department.faculty_id === parseInt(facultyId)) {
      let option = document.createElement("option");
      option.setAttribute("value", department.id);
      option.innerHTML = department.name;
      if (parseInt(localStorage.getItem("departmentId")) === department.id) {
        option.setAttribute("selected", "");
      }
      container.appendChild(option);
    }
  }
  localStorage.setItem("facultyId", parseInt(facultyId));
  if (!(endpoint in secondaryEndpoints)) {
    fetchSuggestions("")
  }
}

$(".facultySelect").on("change", (e) => {
  setDepartments(e.target.value);
});
$(".departmentSelect").on("change", (e) => {
  localStorage.setItem("departmentId", parseInt(e.target.value));
  if (!(endpoint in secondaryEndpoints)) {
    fetchSuggestions("")
  }
});
$(".departmentSelect").on("click", (e) => {
  $(this).trigger('change');
})

var departments = [];

$.ajax({
  url: "/api/departments",
  type: "GET",
  dataType: "json",
  success: function (data) {
    data = data["items"];
    $(".facultySelect").html("");
    let selectedFaculty = null;
    let container = $(".facultySelect").get(0);
    for (let i = 0; i < data["faculties"].length; i++) {
      let option = document.createElement("option");
      option.innerHTML = data["faculties"][i]["name"];
      option.setAttribute("value", data["faculties"][i]["id"]);
      if (
        parseInt(localStorage.getItem("facultyId")) ===
        parseInt(data["faculties"][i]["id"])
      ) {
        option.setAttribute("selected", "");
        selectedFaculty = data["faculties"][i]["id"];
      }
      container.appendChild(option);
    }
    departments = data["departments"];
    if (selectedFaculty) {
      setDepartments(selectedFaculty);
    }
  },
  error: function (xhr, status, error) {
    flash("Ошибка: " + error);
  },
});

let timeoutId;
const searchInput = document.querySelector(".searchField");

searchInput.addEventListener("input", function () {
  clearTimeout(timeoutId);
  timeoutId = setTimeout(function () {
    const query = searchInput.value.trim();
    if (query.length > 0) {
      fetchSuggestions(query);
    } else {
      document.querySelector(".authorList").innerHTML = "";
    }
  }, 500);
});

function fetchSuggestions(query) {
  $.ajax({
    url: "/views/author_list",
    type: "GET",
    dataType: "html",
    data: {
      "q": query,
      "department": localStorage.getItem("departmentId")
    },
    success: function (data) {
      document.querySelector(".authorList").innerHTML = "";
      document.querySelector(".authorList").innerHTML = data;
      setAuthorInfo();
    },
    error: function (xhr, status, error) {
      flash("Ошибка: " + error);
    },
  });
}

let selectedAuthorItem = undefined;

function setAuthorInfo() {
  $(".authorList").off("click");
  $(".authorList").on("click", (e) => {
    let author_id = e.target.getAttribute("data-author-id");
    if (selectedAuthorItem !== undefined) {
      selectedAuthorItem.classList.remove("active");
    }
    selectedAuthorItem = e.target;
    selectedAuthorItem.classList.add("active");
    $.ajax({
      url: "/views/author_info",
      type: "GET",
      data: {
        "author_id": author_id
      },
      dataType: "html",
      success: function (data) {
        document.querySelector(".publView").innerHTML = data;
      },
      error: function (xhr, status, error) {
        flash("Ошибка: " + error);
      },
    });
  })
}

function addTag(tagName, tagContainerId) {
    if (tagName.trim() === '') return;
    var $tag = $('<span class="badge text-bg-primary">' + tagName + '<i class="removeTag ri-close-line"></i></span>');
    $(`#${tagContainerId}`).append($tag);
}

function updateTagList(tagContainerId) {
   let tagNames = [];
    $(`#${tagContainerId} .badge`).each(function () {
      tagNames.push($(this).text().trim());
    });
    return tagNames
}

function updateAliasList() {
   let tagNames = [];
    $(`#aliasesContainer .badge`).each(function () {
      tagNames.push($(this).text().trim());
    });
    return tagNames
}

function addAlias(aliasName) {
    if (aliasName.trim() === '') return;
    var $tag = $('<span class="badge text-bg-secondary">' + aliasName + '<i class="removeAlias ri-close-line"></i></span>');
    $(`#aliasesContainer`).append($tag);
}

$(document).on('input', '.tagsAddField',function () {
    let query = $(this).val().trim();
      $.ajax({
        url: '/api/tags',
        method: 'GET',
        data: { q: query },
        success: function (response) {
          var datalist = $('#tagsList');
          datalist.empty();
          response["items"].forEach(function (tag) {
            datalist.append('<option value="' + tag["name"] + '">');
          });
        },
        error: function () {
          flash('Ошибка получения подсказок');
        }
      });
});

$(document).on('keydown', '.tagsAddField', function (e) {
    if (e.keyCode === 13) {
      e.preventDefault();
      addTag($(this).val(), e.target.getAttribute("data-for"));
      $(this).val('');
    }
});

$(document).on('keydown', '#nameAliases', function (e) {
    if (e.keyCode === 13) {
      e.preventDefault();
      addAlias($(this).val());
      $(this).val('');
    }
});

$(document).on('click', '.removeTag', function () {
    $(this).parent().remove();
});

$(document).on('click', '.removeAlias', function () {
    $(this).parent().remove();
});

$(document).on('submit', 'form', function (e) {
  e.preventDefault();
});

if (!(endpoint in secondaryEndpoints)) {
  $(document).on("click", "#saveRecordBtn", () => {
    let fullName = $('#fullName').val();
    let lastNameInitials = $('#lastNameInitials').val();
    let department = $('#department').val();
    let tags = updateTagList("editTagsContainer")
    let nameAliases = updateAliasList();

    var data = {
      id: document.querySelector('[data-current-author-id]').getAttribute("data-current-author-id"),
      full_name: fullName,
      library_name: lastNameInitials,
      department_id: department,
      tags: tags.join(","),
      aliases: nameAliases.join(",")
    };

    $.ajax({
      url: '/api/authors/change/',
      method: 'POST',
      data: data,
      success: function (response) {
        flash("Данные успешно сохранены")
      },
      error: function () {
        flash("Данные не удалось сохранить")
      }
    });
  });

  $(document).on("click", "#removeRecordBtn", () => {
    $.ajax({
      url: '/api/authors/delete/',
      method: 'POST',
      data: {"id":document.querySelector('[data-current-author-id]').getAttribute("data-current-author-id")},
      success: function (response) {
        flash("Данные успешно сохранены")
      },
      error: function () {
        flash("Данные не удалось сохранить")
      }
    });
  })

  $('#addPersonBtn').click(function () {
      var fullName = $('#fullName').val();
      var lastNameInitials = $('#lastNameInitials').val();
      var department = $('#department').val();
      var tags = updateTagList("addPersonTagsContainer");

      var data = {
        full_name: fullName,
        library_primary_name: lastNameInitials,
        department_id: department,
        tags_list: tags.join(",")
      };

      $.ajax({
        url: '/api/authors/add/',
        method: 'POST',
        data: data,
        success: function (response) {
           $('#addPersonModal').modal('hide');
        },
        error: function () {
          flash("Ошибка при добавлении");
        }
      });
  });
}


