from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g
from vatic.vatic import vatic_page


app = Flask('tpod')
app.register_blueprint(vatic_page)



