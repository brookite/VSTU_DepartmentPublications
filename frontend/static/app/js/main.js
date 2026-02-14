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

function flash(text) {
    let id = Math.floor(Math.random() * 10000);
    const body = `
    <div id="${id}" class="toast align-items-center text-bg-primary border-0" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">
          ${text}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
    `;
    document.querySelector(".toast-container").innerHTML += body;
    let toast = new bootstrap.Toast(document.getElementById(id));
    toast.show();
}

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
  $("#addDepartment").val(parseInt(localStorage.getItem("departmentId")));
  localStorage.setItem("facultyId", parseInt(facultyId));
  if (
    departments.length > 0 &&
    !departments
      .filter((d) => d.id == parseInt(localStorage.getItem("departmentId")) 
        && d.faculty_id == parseInt(facultyId)).length
  ) {
    localStorage.setItem('departmentId', parseInt(departments[0].id));
  }
  if (!secondaryEndpoints.includes(endpoint)) {
    fetchSuggestions('');
  }
}

$(".facultySelect").on("change", (e) => {
  setDepartments(e.target.value);
});
$(".departmentSelect").on("change", (e) => {
  localStorage.setItem("departmentId", parseInt(e.target.value));
  if (!(secondaryEndpoints.includes(endpoint))) {
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


function fetchSuggestions(query) {
  $.ajax({
    url: "/views/author_list",
    type: "GET",
    dataType: "html",
    traditional : true,
    data: {
        "q": query,
        "department": localStorage.getItem("departmentId"),
        "tags": updateTagList("searchFilterTagsContainer")
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
        $('.publView').html(data);
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

let debounceTimeout;

$(document).on('input', '#addLastNameInitials', function () {
    clearTimeout(debounceTimeout);

    let query = $(this).val().trim();

    debounceTimeout = setTimeout(function () {
        if (query) {
            $.ajax({
                url: '/api/authorSuggestions',
                method: 'GET',
                data: { q: query },
                success: function (response) {
                    var datalist = $('#authorList');
                    datalist.empty();
                    response.forEach(function (tag) {
                        datalist.append('<option value="' + tag + '">');
                    });
                },
                error: function () {
                    flash('Ошибка получения подсказок');
                }
            });
        }
    }, 300);
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

if (!(secondaryEndpoints.includes(endpoint))) {
   const searchInput = document.querySelector(".searchField");

    searchInput.addEventListener("input", function () {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(function () {
        const query = searchInput.value.trim();
        fetchSuggestions(query);
      }, 500);
    });

    $(document).on("click", "#resetFilterBtn", () => {
        $("#tagsFilter").val("");
        $("#searchFilterTagsContainer").empty();
    });

    $(document).on("click", ".removeTag", () => {
        fetchSuggestions($(".searchField").val());
    });

    $(document).on('keydown', '#tagsFilter', function (e) {
        if (e.keyCode === 13) {
          e.preventDefault();
          fetchSuggestions($(".searchField").val());
        }
    });

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
      tags: tags,
      aliases: nameAliases
    };

    $.ajax({
      url: '/api/authors/change/',
      method: 'POST', traditional : true,
      data: data,
      success: function (response) {
        flash("Данные успешно сохранены")
      },
      error: function (data) {
        flash("Данные не удалось сохранить");
        data = data.responseJSON;
            if (data["message"] === "Validation Error") {
                for (let field in data["items"]) {
                    for (let message of data["items"][field]) {
                        flash(message);
                    }
                }
            }
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
        window.location.reload();
      },
      error: function () {
        flash("Данные не удалось сохранить")
      }
    });
  })

  $('#addPersonBtn').click(function () {
      var fullName = $('#addFullName').val();
      var lastNameInitials = $('#addLastNameInitials').val();
      var department = $('#addDepartment').val();
      var tags = updateTagList("addPersonTagsContainer");

      var data = {
        full_name: fullName,
        library_primary_name: lastNameInitials,
        department_id: department,
        tags_list: tags
      };

      $.ajax({
        url: '/api/authors/add/',
        method: 'POST',
        data: data,
          traditional : true,
        success: function (response) {
           $('#addPersonModal').modal('hide');
           window.location.reload();
        },
        error: function (data) {
            flash("Ошибка при добавлении");
            data = data.responseJSON;
            if (data["message"] === "Validation Error") {
                for (let field in data["items"]) {
                    for (let message of data["items"][field]) {
                        flash(message);
                    }
                }
            }
        }
      });
  });
}

$(".rescheduleBtn").on("click", function () {
  $.ajax({
        url: '/api/plan/update_plan/',
        method: 'POST',
        data: {
          "updateInterval": $("#updateInterval").val(),
          "dayOfWeek": $("#dayOfWeek").val(),
          "updateTime": $("#updateTime").val()
        },
        success: function (response) {
           $('#autoUpdateModal').modal('hide');
        },
        error: function () {
          flash("Ошибка при изменении расписания");
        }
      });
})

$(".subscribeEmail").on("click", function () {
    let email_value = $("#email").val().trim();
    if (email_value.length === 0) {
        return;
    }
    $.ajax({
        url: '/api/subscribeEmail',
        method: 'POST',
        traditional : true,
        data: {
            "email": email_value,
            "department": localStorage.getItem("departmentId") == undefined ? -1 : localStorage.getItem("departmentId"),
            "tags": updateTagList("emailTagsContainer")
        },
        success: function (response) {
            if (response["type"] !== "error") {
               if (response["items"]["changed"]) {
                   if (response["items"]["subscribe_status"]) {
                       flash("Вы успешно подписаны на рассылку по электронной почте");
                   } else {
                       flash("Вы отписались от рассылки обновлений по электронной почте");
                   }
               } else {
                   flash("Не удалось изменить состояние подписки на рассылку по электронной почте");
               }
           } else {
               flash("Ошибка при получении информации о подписке")
           }
        },
        error: function () {
          flash("Ошибка при получении информации о подписке. Проверьте правильность введенной почты");
        }
      });

});

$(".updateRequestBtn").on("click", function () {
  $.ajax({
        url: '/api/plan/request_update',
        method: 'GET',
        success: function (response) {
            let minutes = Math.floor(response["items"]["update_interval"] / 60);
           if (response["type"] !== "error") {
               if (response["items"]["result"]) {
                   flash(`Обновление успешно запрошено. Оно будет выполнено в течение ${minutes} минут`);
               } else {
                   flash("Обновление нельзя запросить на данный момент. Попробуйте позже");
               }

           } else {
               flash("Ошибка при запросе обновления")
           }
        },
        error: function () {
          flash("Ошибка при изменении расписания");
        }
      });
})

if (endpoint.startsWith("updates")) {
    $.ajax({
        url: '/views/updates_view',
        method: 'GET',
        success: function (response) {
          document.querySelector(".mainView").innerHTML = response;
        },
        error: function () {
          flash('Ошибка получения списка обновлений');
        }
      });

    $('#applyFilterBtn').click(function(event){
                event.preventDefault();

                var formData = {
                    'department_id': localStorage.getItem("departmentId"),
                    'assigned_to_department': $('#attachedToDepartment').is(':checked'),
                    'tags': updateTagList("updatesTagsContainer"),
                };

                let datefrom = new Date($('#dateFrom').val()).getTime() / 1000;
                let dateto = new Date($('#dateTo').val()).getTime() / 1000;
                if (!Number.isNaN(datefrom)) {
                    formData["dateFrom"] = datefrom;
                }
                if (!Number.isNaN(dateto)) {
                    formData["dateTo"] = dateto;
                }

                $.ajax({
                    type: 'GET',
                    url: '/views/updates_view',
                    data: formData,
                    dataType: "html",
                    traditional : true,
                    success: function(response) {
                        $('.mainView').html(response);
                    }
                });
            });

    $('#resetFilterBtn').click(function(event){
        event.preventDefault();

        $('#dateFrom').val('');
        $('#dateTo').val('');
        $('#attachedToDepartment').prop('checked', false);
        $('#tags').val('');
        $('#updatesTagsContainer').empty();
    });
}

