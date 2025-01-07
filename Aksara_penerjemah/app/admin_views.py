# File: admin_views.py
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

# Blueprint untuk admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

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
@admin_bp.route('/daftar_varian')
@login_required
def daftar_varian():
    varians = Varian.query.all()
    return render_template('admin/Daftar_varian.html', varians=varians)

@admin_bp.route('/hapus_varian_ajax/<int:id_varian>', methods=['POST'])
@login_required
def hapus_varian_ajax(id_varian):
    """
    Hapus varian (dan semua data yang terkait) setelah verifikasi password, via AJAX.
    JSON input: { "password": "..." }
    JSON output: { "status": "success"/"error", "message": "..." }
    """
    varian = Varian.query.get_or_404(id_varian)

    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'No password provided.'}), 400
    
    password_input = data['password']

    # Cek password
    if not check_password_hash(current_user.kata_sandi, password_input):
        return jsonify({'status': 'error', 'message': 'Password salah. Gagal menghapus varian.'}), 401

    try:
        # Hapus data Kata & Kalimat yang memakai varian
        Kata.query.filter_by(jenis_varian=varian.nama_varian).delete(synchronize_session=False)
        Kalimat.query.filter_by(jenis_varian=varian.nama_varian).delete(synchronize_session=False)

        # Hapus varian itu sendiri
        db.session.delete(varian)
        db.session.commit()

        return jsonify({'status': 'success',
                        'message': f'Varian "{varian.nama_varian}" dan data terkait berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


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


# ----------------------
# 1) Daftar Kalimat
# ----------------------
@admin_bp.route('/daftar_kalimat', methods=['GET', 'POST'])
@login_required
def daftar_kalimat():
    if request.method == 'POST':
        # Mirip penambahan kata, hanya ganti model = Kalimat
        varians = Varian.query.all()
        max_kelompok = db.session.query(func.max(Kalimat.id_kelompok)).scalar() or 0
        new_kelompok_id = max_kelompok + 1
        kalimat_valid_exists = False

        try:
            for varian in varians:
                konten = request.form.get(f'konten_{varian.nama_varian}', '').strip()
                if not konten:
                    continue

                kalimat_baru = Kalimat(
                    konten=konten,
                    id_kelompok=new_kelompok_id,
                    status_validasi=False,
                    created_by=session.get('id_pengguna'),
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
            logging.error(f'Error menambahkan kalimat: {e}')

        return redirect(url_for('admin.daftar_kalimat'))

    # GET request: Tampilkan data kalimat (pagination)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Kalimat.query.paginate(page=page, per_page=per_page, error_out=False)
    daftar_kalimat = pagination.items
    varians = Varian.query.all()

    return render_template(
        'admin/Daftar_kalimat.html',
        varians=varians,
        daftar_kalimat=daftar_kalimat,
        pagination=pagination
    )


# ----------------------
# 2) Edit Kalimat
# ----------------------
@admin_bp.route('/edit_kalimat/<int:id_kelompok>', methods=['POST'])
def edit_kalimat(id_kelompok):
    kalimat_kelompok = Kalimat.query.filter_by(id_kelompok=id_kelompok).all()
    varians = Varian.query.all()
    
    try:
        for varian in varians:
            konten_baru = request.form.get(f'konten_{varian.nama_varian}', '').strip()
            
            kalimat_item = next((k for k in kalimat_kelompok if k.jenis_varian == varian.nama_varian), None)
            
            if kalimat_item and konten_baru:
                # Update yang sudah ada
                kalimat_item.konten = konten_baru
                kalimat_item.updated_at = datetime.utcnow()
                kalimat_item.updated_by = current_user.id_pengguna
                kalimat_item.status_validasi = False
            elif konten_baru:
                # Jika varian belum punya data, buat baru
                kalimat_baru = Kalimat(
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


# ----------------------
# 3) Hapus Kalimat
# ----------------------
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


# ----------------------
# 4) Pencarian Kalimat
# ----------------------
@admin_bp.route('/cari_kalimat', methods=['GET'])
@login_required
def cari_kalimat():
    kalimat_query = request.args.get('kalimat_query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if kalimat_query:
        query = Kalimat.query.filter(Kalimat.konten.ilike(f'%{kalimat_query}%'))
    else:
        query = Kalimat.query

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    daftar_kalimat = pagination.items
    varians = Varian.query.all()

    return render_template(
        'admin/Daftar_kalimat.html',
        varians=varians,
        daftar_kalimat=daftar_kalimat,
        pagination=pagination,
        kalimat_query=kalimat_query
    )


# ----------------------
# 5) Detail Kalimat (AJAX)
# ----------------------
@admin_bp.route('/detail_kalimat_data/<int:id_kelompok>', methods=['GET'])
@login_required
def detail_kalimat_data(id_kelompok):
    kalimat_list = Kalimat.query.filter_by(id_kelompok=id_kelompok).all()
    varians = Varian.query.all()

    data_detail = []
    for item in kalimat_list:
        data_detail.append({
            'konten': item.konten,
            'jenis_varian': item.jenis_varian,
            'status_validasi': item.status_validasi
        })

    data_varians = [v.nama_varian for v in varians]

    return jsonify({
        'detail_kalimat': data_detail,
        'varians': data_varians
    })


# ----------------------
# 6) Export CSV (Kalimat)
# ----------------------
@admin_bp.route('/export_kalimat/csv', methods=['GET'])
def export_kalimat_csv():
    varians = Varian.query.all()
    daftar_kalimat = Kalimat.query.all()

    if not varians or not daftar_kalimat:
        return Response("Tidak ada data kalimat untuk diekspor.", status=400, mimetype="text/plain")

    header = [varian.nama_varian for varian in varians]

    # Mengelompokkan kalimat berdasarkan id_kelompok
    kelompok_ids = set(k.id_kelompok for k in daftar_kalimat)
    rows = []

    for id_kel in kelompok_ids:
        row = []
        for var in varians:
            kalimat_item = next(
                (k.konten for k in daftar_kalimat 
                 if k.id_kelompok == id_kel and k.jenis_varian == var.nama_varian),
                "-"
            )
            row.append(kalimat_item)
        rows.append(row)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(rows)

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=daftar_kalimat.csv"}
    )


# ----------------------
# 7) Import CSV (Kalimat)
# ----------------------
@admin_bp.route('/import_kalimat/csv', methods=['POST'])
def import_kalimat_csv():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Tidak ada file yang diunggah.'}), 400

    uploaded_file = request.files['file']
    if not uploaded_file.filename.endswith('.csv'):
        return jsonify({'status': 'error', 'message': 'File harus berformat CSV.'}), 400

    try:
        file_content = uploaded_file.stream.read().decode('utf-8')
        csv_reader = csv.reader(io.StringIO(file_content))

        header = next(csv_reader)
        header = [h.strip() for h in header]

        daftar_varian = [v.nama_varian for v in Varian.query.all()]
        kolom_valid = [h for h in header if h in daftar_varian]

        if len(kolom_valid) < 2:
            return jsonify({'status': 'error', 'message': 'Minimal 2 kolom varian yang valid.'}), 400

        total_rows = 0
        for row in csv_reader:
            if len(row) != len(header):
                continue

            max_kelompok = db.session.query(func.max(Kalimat.id_kelompok)).scalar() or 0
            new_kelompok_id = max_kelompok + 1

            for idx, kol in enumerate(header):
                if kol in kolom_valid:
                    konten = row[idx].strip()
                    if konten:
                        kalimat_baru = Kalimat(
                            konten=konten,
                            id_kelompok=new_kelompok_id,
                            jenis_varian=kol,
                            status_validasi=False,
                            created_by=current_user.id_pengguna,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(kalimat_baru)
                        total_rows += 1

        db.session.commit()
        return jsonify({'status': 'success', 'message': f'{total_rows} kalimat berhasil diimpor.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Gagal mengimpor CSV: {str(e)}'}), 500



# ----------------------
# 8) Hapus Terpilih (Mass Delete)
# ----------------------
@admin_bp.route('/hapus_terpilih_kalimat', methods=['POST'])
@login_required
def hapus_terpilih_kalimat():
    data = request.get_json()
    if not data or 'selected_ids' not in data:
        return jsonify({'status': 'error', 'message': 'Tidak ada data ID terpilih.'}), 400

    list_ids = data['selected_ids']
    if not list_ids:
        return jsonify({'status': 'error', 'message': 'List ID kosong.'}), 400

    try:
        Kalimat.query.filter(Kalimat.id_kalimat.in_(list_ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'{len(list_ids)} kalimat berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/Daftar_kata', methods=['GET', 'POST'])
@login_required
def daftarkata():
    
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
    per_page = 10
    pagination = Kata.query.paginate(page=page, per_page=per_page, error_out=False)
    daftar_kata = pagination.items
    varians = Varian.query.all()
    detail_id = None  # atau definisikan sesuai kebutuhan

    
    return render_template(
        'admin/Daftar_kata.html',
    daftar_kata=daftar_kata,
    pagination=pagination,
    varians=varians,
    detail_id=None,        # Jangan diisi apa pun selain None
    detail_kata=[]
    )
    
@admin_bp.route('/cari_kata', methods=['GET'])
@login_required
def cari_kata():
    """
    Route khusus untuk pencarian kata via GET
    """
    kata_query = request.args.get('kata_query', '').strip()
    varians = Varian.query.all()
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if kata_query:
        # Gunakan ilike untuk case-insensitive
        query = Kata.query.filter(Kata.konten.ilike(f'%{kata_query}%'))
    else:
        # Jika tidak ada pencarian, kembalikan semua
        query = Kata.query
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    daftar_kata = pagination.items
    
    return render_template(
        'admin/Daftar_kata.html',
        varians=varians,
        daftar_kata=daftar_kata,
        pagination=pagination,
        kata_query=kata_query  # Kirim kata_query ke template (opsional, utk menampilkan kembali di input)
    )

@admin_bp.route('/detail_kata_data/<int:id_kelompok>', methods=['GET'])
@login_required
def detail_kata_data(id_kelompok):
    """
    Route khusus untuk mengembalikan detail kata (berdasarkan id_kelompok) dalam format JSON,
    sehingga dapat diakses via AJAX tanpa pindah page.
    """
    # Query data detail
    detail_kata = Kata.query.filter_by(id_kelompok=id_kelompok).all()
    varians = Varian.query.all()

    # Susun data JSON
    data_detail = []
    for item in detail_kata:
        data_detail.append({
            'konten': item.konten,
            'jenis_varian': item.jenis_varian,
            'status_validasi': item.status_validasi
        })

    # Kita juga kirim daftar varian agar front-end bisa menampilkan urutan varian
    data_varians = [v.nama_varian for v in varians]

    return jsonify({
        'detail_kata': data_detail,
        'varians': data_varians
    })


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


# Fitur Eksport Kata ke CSV
@admin_bp.route('/export/csv', methods=['GET'])
def export_csv():
    # Ambil data varians dan daftar kata dari database
    varians = Varian.query.all()
    daftar_kata = Kata.query.all()

    if not varians or not daftar_kata:  # Cek jika data kosong
        return Response(
            "Tidak ada data untuk diekspor.",
            status=400,
            mimetype="text/plain"
        )

    # Membuat header CSV berdasarkan nama varians
    header = [varian.nama_varian for varian in varians]

    # Mengelompokkan kata berdasarkan id_kelompok
    kelompok_ids = set(kata.id_kelompok for kata in daftar_kata)
    rows = []

    for id_kelompok in kelompok_ids:
        row = []
        for varian in varians:
            # Filter kata sesuai id_kelompok dan jenis_varian
            kata = next(
                (
                    k.konten
                    for k in daftar_kata
                    if k.id_kelompok == id_kelompok and k.jenis_varian == varian.nama_varian
                ),
                "-",  # Default jika tidak ada kata
            )
            row.append(kata)
        rows.append(row)

    # Membuat CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)  # Tulis header
    writer.writerows(rows)  # Tulis data

    # Return sebagai respons
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=daftar_kata.csv"},
    )

# Akhir Fitur Ekspor ke CSV

# Rute untuk mengunggah file CSV
@admin_bp.route('/import/csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Tidak ada file yang diunggah.'}), 400

    uploaded_file = request.files['file']
    if not uploaded_file.filename.endswith('.csv'):
        return jsonify({'status': 'error', 'message': 'File harus berformat CSV.'}), 400

    try:
        file_content = uploaded_file.stream.read().decode('utf-8')
        csv_reader = csv.reader(io.StringIO(file_content))

        # Membaca header CSV
        header = next(csv_reader)
        daftar_varian = [varian.nama_varian for varian in Varian.query.all()]  # Validasi kolom
        kolom_valid = [h for h in header if h in daftar_varian]

        if len(kolom_valid) < 2:
            return jsonify({'status': 'error', 'message': 'Minimal 2 kolom varian yang valid.'}), 400

        total_rows = 0
        for row in csv_reader:
            if len(row) != len(header):
                continue

            max_kelompok = db.session.query(func.max(Kata.id_kelompok)).scalar() or 0
            new_kelompok_id = max_kelompok + 1

            for idx, kol in enumerate(header):
                if kol in kolom_valid:
                    konten = row[idx].strip()
                    if konten:
                        kata_baru = Kata(
                            konten=konten,
                            id_kelompok=new_kelompok_id,
                            jenis_varian=kol,
                            status_validasi=False,
                            created_by=current_user.id_pengguna,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(kata_baru)
                        total_rows += 1

        db.session.commit()
        return jsonify({'status': 'success', 'message': f'{total_rows} kata berhasil diimpor.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Gagal mengimpor CSV: {str(e)}'}), 500


# Rute untuk menyimpan data ke database setelah konfirmasi
@admin_bp.route('/import/csv/confirm', methods=['POST'])
def confirm_import_csv():
    data = request.json

    # Validasi data
    if not data or 'rows' not in data or 'valid_columns' not in data:
        return jsonify({'status': 'error', 'message': 'Data tidak valid.'}), 400

    rows = data['rows']
    valid_columns = data['valid_columns']

    # Menambahkan data ke database
    for row in rows:
        for idx, column in enumerate(valid_columns):
            kata = Kata(
                konten=row[idx],
                jenis_varian=column,
                id_kelompok=1  # Misalkan semua data baru masuk kelompok default
            )
            db.session.add(kata)

    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Data berhasil diimpor ke database.'})

@admin_bp.route('/hapus_terpilih', methods=['POST'])
@login_required
def hapus_terpilih():
    """
    Menerima daftar id_kata melalui AJAX (JSON), lalu menghapusnya tanpa reload.
    """
    data = request.get_json()
    if not data or 'selected_ids' not in data:
        return jsonify({'status': 'error', 'message': 'Tidak ada data ID terpilih.'}), 400

    list_ids = data['selected_ids']  # ex: [3, 5, 10]
    if not list_ids:
        return jsonify({'status': 'error', 'message': 'Daftar ID kosong.'}), 400

    try:
        # Hapus data yang ada di list
        Kata.query.filter(Kata.id_kata.in_(list_ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'{len(list_ids)} data berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500



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

    return redirect(url_for('admin.kelola_user'))