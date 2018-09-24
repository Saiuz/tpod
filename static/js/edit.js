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
// using jQuery
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

    $(".edit-form").submit(function (event) {
        event.preventDefault()
        var first_name = $(".edit-form-first-name")[0].value;
        var last_name = $(".edit-form-last-name")[0].value;
        var age = $(".edit-form-age")[0].value;
        var bio = $(".edit-form-bio")[0].value;
        var avatar = $(".edit-form-avatar")[0].files[0];

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
        if (check_input("first name", first_name) ||
            check_input("last name", last_name)) {
            event.preventDefault()
            return false;
        }
        var input_img = $(".edit-form-avatar")[0].files[0];
        if (input_img != undefined && !(input_img.name.toString().toLowerCase().endsWith(".png") ||
            input_img.name.toString().toLowerCase().endsWith(".jpg") ||
            input_img.name.toString().toLowerCase().endsWith(".jpeg"))) {
            alert("The file you selected is not valid image !")
            event.preventDefault()
            return false;
        }
        var formData = new FormData();

        formData.append('first_name', first_name);
        formData.append('last_name', last_name);
        formData.append('age', age);
        formData.append('bio', bio);
        formData.append('avatar', avatar);

        var success_callback = function (response) {
            var obj = JSON.parse(JSON.stringify(response));
            if (obj.status == 1) {
                location.href = obj.redirect;
            } else {
                alert("failure " + obj.msg);
            }
        };

        $.ajax({
            url: "/profile_edit",
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
