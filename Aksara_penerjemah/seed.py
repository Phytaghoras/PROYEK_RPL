from app import create_app
from app.models import db, Pengguna
from werkzeug.security import generate_password_hash

# Membuat aplikasi Flask
app = create_app()

# Data admin yang akan ditambahkan
admin_data = {
    "nama_pengguna": "password",  # Nama pengguna admin, bisa diubah
    "kata_sandi": "password",       # Kata sandi admin (akan dienkripsi)
    "peran": "admin"
}

with app.app_context():
    # Menambahkan admin jika belum ada
    admin = Pengguna.query.filter_by(nama_pengguna=admin_data["nama_pengguna"]).first()
    if not admin:
        hashed_password = generate_password_hash(admin_data["kata_sandi"], method='pbkdf2:sha256')
        new_admin = Pengguna(
            nama_pengguna=admin_data["nama_pengguna"],
            kata_sandi=hashed_password,
            peran=admin_data["peran"]
        )
        db.session.add(new_admin)
        print(f"Menambahkan pengguna admin dengan nama pengguna: {admin_data['nama_pengguna']}")
    else:
        print("Pengguna admin sudah ada di database.")

    # Menyimpan perubahan ke database
    db.session.commit()
    print("Pengguna admin berhasil ditambahkan ke database jika belum ada.")
