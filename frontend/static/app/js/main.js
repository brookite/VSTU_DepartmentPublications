const endpoint = window.location.href.split('?')[0].split('/').at(-1);
const secondaryEndpoints = ["updates"]

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

function setAuthorInfo() {
  $(".authorList").off("click");
  $(".authorList").on("click", (e) => {
    let author_id = e.target.getAttribute("data-author-id");
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




