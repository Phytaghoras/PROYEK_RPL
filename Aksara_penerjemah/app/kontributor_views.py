# File: kontributor_views.py
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

# Blueprint untuk kontributor routes
kontributor_bp = Blueprint('kontributor', __name__, url_prefix='/kontributor')


# Dashboard Kontributor
@kontributor_bp.route('/dashboard')
def kontributor_dashboard():
    if 'user_id' not in session or session.get('role') != 'kontributor':
        return redirect(url_for('main.login'))
    return render_template('kontributor/Kontributor_dashboard.html')