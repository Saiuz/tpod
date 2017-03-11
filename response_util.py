from flask import jsonify


def json_success_response(redirect=''):
    ret = {
            "status": 1,
            "msg": "success",
            "redirect":redirect
    }
    return jsonify(ret)


def json_error_response(status = 2, msg='failure'):
    ret = {
            "status": status,
            "msg": msg,
            "redirect":"/"
    }
    return jsonify(ret)

