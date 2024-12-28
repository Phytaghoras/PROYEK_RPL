from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from .models import db, Pengguna, Kata, Kalimat, LogAktivitas, Varian, Kata , Kalimat
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .utils import role_required
from sqlalchemy import func
from flask_login import login_required, login_user, logout_user, current_user
import logging

# Blueprint untuk main routes
main = Blueprint('main', __name__)

# Blueprint untuk admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Blueprint untuk validator routes
validator_bp = Blueprint('validator', __name__, url_prefix='/validator')

# Blueprint untuk kontributor routes
kontributor_bp = Blueprint('kontributor', __name__, url_prefix='/kontributor')

# Route Login
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

# Dashboard Admin
@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    jumlah_kata=Kata.query.count()
    jumlah_kalimat=Kalimat.query.count()
    jumlah_varian=Varian.query.count()

    return render_template('admin/Admin_dashboard.html',
                           jumlah_kata=jumlah_kata,
                           jumlah_kalimat=jumlah_kalimat,
                           jumlah_varian=jumlah_varian)

@role_required('admin')
@login_required
@admin_bp.route('/daftar_varian')
def daftar_varian():
    varians = Varian.query.all()
    return render_template('admin/Daftar_varian.html', varians=varians)

@admin_bp.route('/tambah_varian', methods=['POST'])
def tambah_varian():
    nama_varian = request.form.get('nama_varian')
    
    # Cek apakah varian sudah ada
    existing_varian = Varian.query.filter_by(nama_varian=nama_varian).first()
    
    if existing_varian:
        flash('Varian sudah ada.', 'danger')
    else:
        try:
            varian_baru = Varian(nama_varian=nama_varian)
            db.session.add(varian_baru)
            db.session.commit()
            flash('Varian berhasil ditambahkan.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan varian: {str(e)}', 'danger')
    
    return redirect(url_for('admin.daftar_varian'))

@admin_bp.route('/edit_varian/<int:id_varian>', methods=['POST'])
def edit_varian(id_varian):
    varian = Varian.query.get_or_404(id_varian)
    nama_varian_baru = request.form.get('nama_varian')
    
    try:
        varian.nama_varian = nama_varian_baru
        db.session.commit()
        flash('Varian berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui varian: {str(e)}', 'danger')
    
    return redirect(url_for('admin.daftar_varian'))

@admin_bp.route('/hapus_varian/<int:id_varian>', methods=['POST'])
def hapus_varian(id_varian):
    varian = Varian.query.get_or_404(id_varian)
    
    try:
        db.session.delete(varian)
        db.session.commit()
        flash('Varian berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus varian: {str(e)}', 'danger')
    
    return redirect(url_for('admin.daftar_varian'))

@admin_bp.route('/kelola_user')
def kelola_user():
    users = Pengguna.query.all()  # Semua data user
    return render_template('admin/Kelola_user.html', users=users)


@admin_bp.route('/daftar_kalimat', methods=['GET', 'POST'])
def daftar_kalimat():
    if request.method == 'POST':
        # Generate id_kelompok baru
        max_kelompok = db.session.query(func.max(Kalimat.id_kelompok)).scalar() or 0
        new_kelompok_id = max_kelompok + 1

        varians = Varian.query.all()
        kalimat_valid_exists = False

        try:
            for varian in varians:
                konten = request.form.get(f'konten_{varian.nama_varian}', '').strip()
                
                if konten:
                    kalimat_baru = Kalimat(
                        konten=konten,
                        id_kelompok=new_kelompok_id,
                        status_validasi=False,
                        created_by=current_user.id_pengguna,
                        created_at=datetime.utcnow(),
                        jenis_varian=varian.nama_varian
                    )
                    db.session.add(kalimat_baru)
                    kalimat_valid_exists = True

            if kalimat_valid_exists:
                db.session.commit()
                flash('Kalimat berhasil ditambahkan.', 'success')
            else:
                flash('Tidak ada kalimat yang valid untuk disimpan.', 'warning')

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan kalimat: {str(e)}', 'danger')

    # Bagian GET request
    page = request.args.get('page', 1, type=int)
    per_page = 100
    pagination = Kalimat.query.paginate(page=page, per_page=per_page, error_out=False)
    daftar_kalimat = pagination.items
    varians = Varian.query.all()

    return render_template('admin/Daftar_kalimat.html', 
                           varians=varians, 
                           daftar_kalimat=daftar_kalimat, 
                           pagination=pagination)



@admin_bp.route('/edit_kalimat/<int:id_kelompok>', methods=['POST'])
def edit_kalimat(id_kelompok):
    # # Ambil semua kalimat dalam kelompok yang sama
    # kalimat_kelompok = Kalimat.query.filter_by(id_kelompok=id_kelompok).all()
    # varians = Varian.query.all()
    
    # try:
    #     for varian in varians:
    #         konten_baru = request.form.get(f'konten_{varian.nama_varian}', '').strip()
            
    #         # Cari kalimat spesifik untuk varian ini
    #         kalimat = next((k for k in kalimat_kelompok if k.jenis_varian == varian.nama_varian), None)
            
    #         if kalimat and konten_baru:
    #             # Update kalimat yang sudah ada
    #             kalimat.konten = konten_baru
    #             kalimat.updated_at = datetime.utcnow()
    #             kalimat.updated_by = current_user.id_pengguna
    #             kalimat.status_validasi = False
    #         elif konten_baru:
    #             # Jika varian belum punya kalimat, buat kalimat baru
    #             kalimat_baru = Kalimat(
    #                 konten=konten_baru,
    #                 id_kelompok=id_kelompok,
    #                 jenis_varian=varian.nama_varian,
    #                 status_validasi=False,
    #                 created_by=current_user.id_pengguna,
    #                 created_at=datetime.utcnow()
    #             )
    #             db.session.add(kalimat_baru)
        
    #     db.session.commit()
    #     flash('Kalimat berhasil diperbarui.', 'success')
    # except Exception as e:
    #     db.session.rollback()
    #     flash(f'Gagal memperbarui kalimat: {str(e)}', 'danger')
    
    # return redirect(url_for('admin.daftar_kalimat'))

    # Ambil semua kata dalam kelompok yang sama
    kalimat_kelompok = Kalimat.query.filter_by(id_kelompok=id_kelompok).all()
    varians = Varian.query.all()
    
    try:
        for varian in varians:
            konten_baru = request.form.get(f'konten_{varian.nama_varian}', '').strip()
            
            # Cari kata spesifik untuk varian ini
            kalimat = next((k for k in kalimat_kelompok if k.jenis_varian == varian.nama_varian), None)
            
            if kalimat and konten_baru:
                # Update kata yang sudah ada
                kalimat.konten = konten_baru
                kalimat.updated_at = datetime.utcnow()
                kalimat.updated_by = current_user.id_pengguna
                kalimat.status_validasi = False
            elif konten_baru:
                # Jika varian belum punya kata, buat kata baru
                kalimat_baru = kalimat(
                    konten=konten_baru,
                    id_kelompok=id_kelompok,
                    jenis_varian=varian.nama_varian,
                    status_validasi=False,
                    created_by=current_user.id_pengguna,
                    created_at=datetime.utcnow()
                )
                db.session.add(kalimat_baru)
        
        db.session.commit()
        flash('Kalimat berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui kalimat: {str(e)}', 'danger')
    
    return redirect(url_for('admin.daftar_kalimat'))

@admin_bp.route('/hapus_kalimat/<int:id_kalimat>', methods=['POST'])
def hapus_kalimat(id_kalimat):
    kalimat = Kalimat.query.get_or_404(id_kalimat)
    try:
        db.session.delete(kalimat)
        db.session.commit()
        flash('Kalimat berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.daftar_kalimat'))


@admin_bp.route('/Daftar_kata', methods=['GET', 'POST'])
@login_required
def daftarkata():
    # # Validasi role Admin
    # if session.get('role') != 'Admin':
        # flash('Anda tidak memiliki akses ke halaman ini.', 'danger')      # Kode ini masih ada masalah
    #     return redirect(url_for('main.login'))

    if request.method == 'POST':
        varians = Varian.query.all()
        max_kelompok = db.session.query(func.max(Kata.id_kelompok)).scalar() or 0
        new_kelompok_id = max_kelompok + 1
        kata_valid_exists = False

        try:
            for varian in varians:
                konten = request.form.get(f'konten_{varian.nama_varian}', '').strip()
                if not konten:
                    continue  # Abaikan input kosong

                kata_baru = Kata(
                    konten=konten,
                    id_kelompok=new_kelompok_id,
                    status_validasi=False,
                    created_by=session.get('id_pengguna'),  # Ambil dari session
                    created_at=datetime.utcnow(),
                    jenis_varian=varian.nama_varian
                )
                db.session.add(kata_baru)
                kata_valid_exists = True

            if kata_valid_exists:
                db.session.commit()
                flash('Kata berhasil ditambahkan.', 'success')
            else:
                flash('Tidak ada kata yang valid untuk disimpan.', 'warning')

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan kata: {str(e)}', 'danger')
            logging.error(f'Error menambahkan kata: {e}')

        return redirect(url_for('admin.daftarkata'))

    # GET Request
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = Kata.query.paginate(page=page, per_page=per_page, error_out=False)
    daftar_kata = pagination.items
    varians = Varian.query.all()

    return render_template(
        'admin/Daftar_kata.html',
        varians=varians,
        daftar_kata=daftar_kata,
        pagination=pagination
    )



@admin_bp.route('/detail_kata/<int:id_kelompok>')
def detail_kata(id_kelompok):
    kata_detail = Kata.query.filter_by(id_kelompok=id_kelompok).all()
    varians = Varian.query.all()
    
    return render_template('admin/modal_detail_kata.html', 
                           kata_detail=kata_detail, 
                           varians=varians)



@admin_bp.route('/edit_kata/<int:id_kelompok>', methods=['POST'])
def edit_kata(id_kelompok):
    # Ambil semua kata dalam kelompok yang sama
    kata_kelompok = Kata.query.filter_by(id_kelompok=id_kelompok).all()
    varians = Varian.query.all()
    
    try:
        for varian in varians:
            konten_baru = request.form.get(f'konten_{varian.nama_varian}', '').strip()
            
            # Cari kata spesifik untuk varian ini
            kata = next((k for k in kata_kelompok if k.jenis_varian == varian.nama_varian), None)
            
            if kata and konten_baru:
                # Update kata yang sudah ada
                kata.konten = konten_baru
                kata.updated_at = datetime.utcnow()
                kata.updated_by = current_user.id_pengguna
                kata.status_validasi = False
            elif konten_baru:
                # Jika varian belum punya kata, buat kata baru
                kata_baru = Kata(
                    konten=konten_baru,
                    id_kelompok=id_kelompok,
                    jenis_varian=varian.nama_varian,
                    status_validasi=False,
                    created_by=current_user.id_pengguna,
                    created_at=datetime.utcnow()
                )
                db.session.add(kata_baru)
        
        db.session.commit()
        flash('Kata berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui kata: {str(e)}', 'danger')
    
    return redirect(url_for('admin.daftarkata'))

@admin_bp.route('/hapus_kata/<int:id_kata>', methods=['POST'])
def hapus_kata(id_kata):
    kata = Kata.query.get_or_404(id_kata)
    try:
        db.session.delete(kata)
        db.session.commit()
        flash('Kata berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.daftarkata'))


@admin_bp.route('/tambah_user', methods=['POST'])
def proses_tambah_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    # Hash password sebelum menyimpan
    hashed_password = generate_password_hash(password)

    # Simpan user baru ke database
    user_baru = Pengguna(
        nama_pengguna=username,
        kata_sandi=hashed_password,
        peran=role
    )
    try:
        db.session.add(user_baru)
        db.session.commit()
        flash('User berhasil ditambahkan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.kelola_user'))


@admin_bp.route('/proses_edit_user', methods=['POST'])
def proses_edit_user():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    user = Pengguna.query.get_or_404(user_id)
    user.nama_pengguna = username
    user.peran = role

    if password:  # Jika password diubah
        user.kata_sandi = generate_password_hash(password)

    try:
        db.session.commit()
        flash('User berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.Kelola_user'))

@validator_bp.route('/dashboard')
def validator_dashboard():
    jumlah_kata=Kata.query.count()
    jumlah_kalimat=Kalimat.query.count()
    jumlah_varian=Varian.query.count()

    return render_template('validator/Validator_dashboard.html',
                           jumlah_kata=jumlah_kata,
                           jumlah_kalimat=jumlah_kalimat,
                           jumlah_varian=jumlah_varian)
# Dashboard Kontributor
@kontributor_bp.route('/dashboard')
def kontributor_dashboard():
    if 'user_id' not in session or session.get('role') != 'kontributor':
        return redirect(url_for('main.login'))
    return render_template('kontributor/Kontributor_dashboard.html')



@validator_bp.route('/validasi', methods=['GET', 'POST'])
def validasi_kata():
    if request.method == 'POST':
        # Ambil ID kata dan aksi dari form
        id_kata = request.form.get('id_kata')
        action = request.form.get('action')

        # Cari kata berdasarkan ID
        kata = Kata.query.get_or_404(id_kata)

        try:
            if action == 'terima':
                # Ubah status validasi menjadi True
                kata.status_validasi = True
                kata.validated_by = current_user.id_pengguna
                kata.validated_at = datetime.utcnow()
                
                # Log aktivitas validasi
                log_validasi = LogAktivitas(
                    id_pengguna=current_user.id_pengguna,
                    jenis_aktivitas='Validasi Kata',
                    detail_aktivitas=f'Kata "{kata.konten}" divalidasi'
                )
                db.session.add(log_validasi)
                
                flash('Kata berhasil divalidasi.', 'success')

            elif action == 'tolak':
                # Hapus kata dari database
                db.session.delete(kata)
                
                # Log aktivitas penolakan
                log_validasi = LogAktivitas(
                    id_pengguna=current_user.id_pengguna,
                    jenis_aktivitas='Penolakan Kata',
                    detail_aktivitas=f'Kata "{kata.konten}" ditolak'
                )
                db.session.add(log_validasi)
                
                flash('Kata berhasil ditolak dan dihapus.', 'warning')

            # Commit perubahan ke database
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')

    # Untuk GET request, ambil daftar kata yang belum divalidasi
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Kata.query.filter_by(status_validasi=False).paginate(page=page, per_page=per_page, error_out=False)
    daftar_kata = pagination.items
    varians = Varian.query.all()

    return render_template('admin/Validator.html', 
                           varians=varians, 
                           daftar_kata=daftar_kata, 
                           pagination=pagination)