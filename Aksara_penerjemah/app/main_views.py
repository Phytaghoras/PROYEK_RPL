# File: auth_views.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session , Response
from .models import db, Pengguna, Kata, Kalimat, LogAktivitas, Varian, Kata , Kalimat
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .utils import role_required
from sqlalchemy import func
from flask_login import login_required, login_user, logout_user, current_user
import logging
import io
import csv

# Blueprint untuk main routes
main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nama_pengguna = request.form['nama_pengguna']
        kata_sandi = request.form['kata_sandi']

        user = Pengguna.query.filter_by(nama_pengguna=nama_pengguna).first()

        if user and check_password_hash(user.kata_sandi, kata_sandi):
            login_user(user)
            if user.peran == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif user.peran == 'validator':
                return redirect(url_for('validator.validator_dashboard'))
            elif user.peran == 'kontributor':
                return redirect(url_for('kontributor.kontributor_dashboard'))
            else:
                flash('Peran pengguna tidak dikenali.')
                return redirect(url_for('main.login'))
        else:
            flash('Login gagal. Nama pengguna atau kata sandi salah.')
            return redirect(url_for('main.login'))

    return render_template('login.html')

# Route Logout
@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))








