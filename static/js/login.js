/*
 * Copyright 2018 Carnegie Mellon University
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Created by suanmiao on 9/18/16.
 */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$(document).ready(function () {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    $("#login-tab-signup").click(function () {
        $("#login-tab-signup").addClass("active");
        $("#login-tab-login").removeClass("active");
        var list = $(".login-form");
        for (var i = list.length - 1; i >= 0; i--) {
            list[i].style.display = "none";
        }
        list = $(".signup-form");
        for (var i = list.length - 1; i >= 0; i--) {
            list[i].style.display = "block";
        }
    })

    $("#login-tab-login").click(function () {
        $("#login-tab-login").addClass("active");
        $("#login-tab-signup").removeClass("active");
        var list = $(".login-form");
        for (var i = list.length - 1; i >= 0; i--) {
            list[i].style.display = "block";
        }
        list = document.getElementsByClassName("signup-form");
        for (var i = list.length - 1; i >= 0; i--) {
            list[i].style.display = "none";
        }
    })
    $("#login-tab-login").trigger("click");

    $(".login-form-confirm").click(function (event) {
        event.preventDefault()
        var formData = new FormData();
        var username = $(".login-form-username")[0].value;
        var password = $(".login-form-password")[0].value;
        var check_input = function (input_name, input) {
            if (input.length == 0) {
                alert("Please input correct " + input_name)
                return true;
            } else if (input.length > 20) {
                alert("The " + input_name + " you input is too long")
                return true;
            }
            return false;
        }
        if (check_input("username", username) || check_input("password", password)) {
            return;
        }
        formData.append('username', username);
        formData.append('password', password);

        var success_callback = function (response) {
            var obj = JSON.parse(JSON.stringify(response));
            if (obj.status == 1) {
                location.href = obj.redirect;
            } else {
                alert("Login failure: " + obj.msg);
            }
        };

        $.ajax({
            url: "/login",
            type: "POST",
            data: formData,
            contentType: false,
            processData: false,
            async: true,
            cache: false,
            success: success_callback,
        });
    });

    return false;
})
