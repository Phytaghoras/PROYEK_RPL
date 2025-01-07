# File: validator_views.py
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

# Blueprint untuk validator routes
validator_bp = Blueprint('validator', __name__, url_prefix='/validator')

@validator_bp.route('/dashboard')
def validator_dashboard():
    jumlah_kata=Kata.query.count()
    jumlah_kalimat=Kalimat.query.count()
    jumlah_varian=Varian.query.count()

    return render_template('validator/Validator_dashboard.html',
                           jumlah_kata=jumlah_kata,
                           jumlah_kalimat=jumlah_kalimat,
                           jumlah_varian=jumlah_varian)

@validator_bp.route('/validasi_data', methods=['GET'])
def validasi_data():
    """
    Mengembalikan data kata atau kalimat yang belum divalidasi, 
    dalam format JSON, sesuai parameter ?tipe=kata/kalimat.
    Contoh: /validator/validasi_data?tipe=kalimat
    """
    tipe = request.args.get('tipe', 'kata')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if tipe == 'kalimat':
        from .models import Kalimat
        query = Kalimat.query.filter_by(status_validasi=False)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        data_items = pagination.items

        # Susun data JSON
        data_list = []
        for item in data_items:
            data_list.append({
                'id': item.id_kalimat,
                'id_kelompok': item.id_kelompok,
                'varian': item.jenis_varian,
                'konten': item.konten,
                'status_validasi': item.status_validasi
            })

        total_pages = pagination.pages
        current_page = pagination.page

        return jsonify({
            'tipe': 'kalimat',
            'items': data_list,
            'current_page': current_page,
            'total_pages': total_pages
        })

    else:
        # Default kata
        from .models import Kata
        query = Kata.query.filter_by(status_validasi=False)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        data_items = pagination.items

        data_list = []
        for item in data_items:
            data_list.append({
                'id': item.id_kata,
                'id_kelompok': item.id_kelompok,
                'varian': item.jenis_varian,
                'konten': item.konten,
                'status_validasi': item.status_validasi
            })

        total_pages = pagination.pages
        current_page = pagination.page

        return jsonify({
            'tipe': 'kata',
            'items': data_list,
            'current_page': current_page,
            'total_pages': total_pages
        })


@validator_bp.route('/validasi_action', methods=['POST'])
def validasi_action():
    """
    Menerima JSON berisi:
    {
      'tipe': 'kata' or 'kalimat',
      'id': <id_kata or id_kalimat>,
      'action': 'terima' or 'tolak'
    }
    lalu mengupdate DB tanpa reload.
    """
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    tipe = data.get('tipe')
    item_id = data.get('id')
    action = data.get('action')

    if not all([tipe, item_id, action]):
        return jsonify({'status': 'error', 'message': 'Incomplete parameters'}), 400

    if tipe == 'kalimat':
        from .models import Kalimat
        kalimat = Kalimat.query.get(item_id)
        if not kalimat:
            return jsonify({'status': 'error', 'message': 'Kalimat not found'}), 404
        
        if action == 'terima':
            kalimat.status_validasi = True
            kalimat.validated_by = current_user.id_pengguna
            kalimat.validated_at = datetime.utcnow()
            
            # Log aktivitas (opsional)
            log_validasi = LogAktivitas(
                id_pengguna=current_user.id_pengguna,
                jenis_aktivitas='Validasi Kalimat',
                detail_aktivitas=f'Kalimat "{kalimat.konten}" divalidasi'
            )
            db.session.add(log_validasi)
            
            message = 'Kalimat berhasil divalidasi.'
        elif action == 'tolak':
            # Hapus kalimat
            db.session.delete(kalimat)
            log_penolakan = LogAktivitas(
                id_pengguna=current_user.id_pengguna,
                jenis_aktivitas='Penolakan Kalimat',
                detail_aktivitas=f'Kalimat ditolak'
            )
            db.session.add(log_penolakan)
            message = 'Kalimat berhasil ditolak dan dihapus.'
        else:
            return jsonify({'status': 'error', 'message': 'Invalid action'}), 400

    else:
        # tipe = 'kata'
        from .models import Kata
        kata = Kata.query.get(item_id)
        if not kata:
            return jsonify({'status': 'error', 'message': 'Kata not found'}), 404
        
        if action == 'terima':
            kata.status_validasi = True
            kata.validated_by = current_user.id_pengguna
            kata.validated_at = datetime.utcnow()
            
            log_validasi = LogAktivitas(
                id_pengguna=current_user.id_pengguna,
                jenis_aktivitas='Validasi Kata',
                detail_aktivitas=f'Kata "{kata.konten}" divalidasi'
            )
            db.session.add(log_validasi)

            message = 'Kata berhasil divalidasi.'
        elif action == 'tolak':
            db.session.delete(kata)
            log_penolakan = LogAktivitas(
                id_pengguna=current_user.id_pengguna,
                jenis_aktivitas='Penolakan Kata',
                detail_aktivitas='Kata ditolak'
            )
            db.session.add(log_penolakan)
            message = 'Kata berhasil ditolak dan dihapus.'
        else:
            return jsonify({'status': 'error', 'message': 'Invalid action'}), 400

    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@validator_bp.route('/validasi')
def validasi_page():
    return render_template('admin/Validator.html')