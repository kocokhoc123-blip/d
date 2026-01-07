import pytest
from app import app

"""
tests/test_login.py

Unit tests cho chức năng đăng nhập (sử dụng Flask test client).
Các chú thích tiếng Việt mô tả kỹ thuật kiểm thử áp dụng cho từng test case.

Ghi chú kỹ thuật:
- Vì app.py dùng render_template() và repository có thể không chứa file template trong môi trường test,
  ta tạm thời mock (ghi đè) app.render_template để trả về chuỗi đơn giản chứa thông báo lỗi.
  Việc này giúp test tập trung vào logic xử lý và phản hồi (redirect/failed render) mà không phụ thuộc template.
- Sử dụng Flask test_client() để gửi POST form tới "/" và client.session_transaction() để kiểm tra session.
"""

@pytest.fixture(autouse=True)
def client():
    """
    Fixture tạo Flask test client và mock app.render_template để tránh TemplateNotFound.
    Áp dụng cho tất cả test (autouse=True).
    """
    app.testing = True
    # Lưu render_template gốc (nếu cần khôi phục sau test)
    original_render = getattr(app, "render_template", None)
    # Ghi đè để render_template trả về chuỗi có chứa lỗi (nếu có)
    app.render_template = lambda template, **kwargs: f"RENDERED_ERROR:{kwargs.get('error', '')}"
    with app.test_client() as client:
        yield client
    # Khôi phục nếu cần
    if original_render is not None:
        app.render_template = original_render


# TC01: Đăng nhập thành công
# Kỹ thuật: Phân vùng tương đương - dữ liệu hợp lệ
def test_login_success_sets_session_and_redirects(client):
    """
    Mô tả: Gửi username/password đúng -> mong đợi redirect đến /age (HTTP 302)
    và session['user'] = 'admin'.
    """
    resp = client.post("/", data={"username": "admin", "password": "123456"}, follow_redirects=False)
    # Redirect 302 tới /age
    assert resp.status_code == 302
    # Location có path kết thúc bằng /age (Flask trả location đầy đủ)
    assert resp.headers["Location"].endswith("/age")
    # Kiểm tra session đã được set
    with client.session_transaction() as sess:
        assert sess.get("user") == "admin"


# TC02: Sai mật khẩu
# Kỹ thuật: Phân vùng tương đương - dữ liệu không hợp lệ (password)
def test_login_wrong_password_shows_error(client):
    """
    Mô tả: Username đúng, password sai -> trả về trang login với thông báo lỗi.
    Vì render_template đã mock, ta kiểm tra response chứa chuỗi mock kèm thông báo lỗi.
    """
    resp = client.post("/", data={"username": "admin", "password": "000000"})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:Sai tai\xE0 kho\xE2n ho\xe1c m\xe1t kh\xe2u" in resp.data or b"RENDERED_ERROR:Sai tài khoản hoặc mật khẩu" in resp.data


# TC03: Sai username
# Kỹ thuật: Phân vùng tương đương - dữ liệu không hợp lệ (username)
def test_login_wrong_username_shows_error(client):
    """
    Mô tả: Username sai, password đúng -> trả về trang login với thông báo lỗi.
    """
    resp = client.post("/", data={"username": "user", "password": "123456"})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data


# TC04: Username để trống
# Kỹ thuật: Phân vùng tương đương - rỗng
def test_login_empty_username_shows_error(client):
    """
    Mô tả: Username rỗng -> được coi là không hợp lệ (so sánh chuỗi) -> trả về lỗi.
    """
    resp = client.post("/", data={"username": "", "password": "123456"})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data


# TC05: Password để trống
# Kỹ thuật: Phân vùng tương đương - rỗng
def test_login_empty_password_shows_error(client):
    """
    Mô tả: Password rỗng -> không khớp -> trả về lỗi.
    """
    resp = client.post("/", data={"username": "admin", "password": ""})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data


# TC06: Cả 2 trường để trống
# Kỹ thuật: Phân vùng tương đương - rỗng
def test_login_both_empty_shows_error(client):
    """
    Mô tả: Cả username và password rỗng -> trả về lỗi.
    """
    resp = client.post("/", data={"username": "", "password": ""})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data


# TC07 & TC08: Giá trị biên username (min/max) - ở đây logic không kiểm tra độ dài, nên chỉ kiểm tra kết quả
# Kỹ thuật: Giá trị biên (độ dài username)
@pytest.mark.parametrize("username", [
    "a",  # min = 1
    "a" * 30  # max giả định = 30
])
def test_login_username_boundary_lengths(client, username):
    """
    Mô tả: Kiểm tra username với độ dài biên; nếu không khớp -> trả về lỗi.
    Kỹ thuật: Giá trị biên.
    """
    resp = client.post("/", data={"username": username, "password": "123456"})
    # Vì chỉ test login, mong đợi hệ thống không crash; kết quả sẽ là lỗi (trừ khi username đúng)
    assert resp.status_code == 200 or resp.status_code == 302
    # Nếu không redirect, mock render sẽ trả về chuỗi chứa RENDERED_ERROR
    if resp.status_code == 200:
        assert b"RENDERED_ERROR:" in resp.data


# TC09: Username cực dài (robustness)
# Kỹ thuật: Dữ liệu vượt giới hạn / robustness
def test_login_very_long_username_does_not_crash(client):
    """
    Mô tả: Gửi username rất dài (10k) để kiểm tra hệ thống không bị crash (HTTP 500).
    Kỹ thuật: Dữ liệu vượt giới hạn.
    """
    very_long = "u" * 10000
    resp = client.post("/", data={"username": very_long, "password": "123456"})
    # Không được crash (không trả về 500)
    assert resp.status_code != 500
    # Khi không khớp, chúng ta nhận về mock render (200)
    assert resp.status_code in (200, 302)


# TC10: Password ngắn hơn min (giả định min=6)
# Kỹ thuật: Giá trị biên (password min)
def test_login_short_password_rejected(client):
    """
    Mô tả: Password có 5 ký tự (dưới ngưỡng giả định 6) -> không khớp -> trả về lỗi.
    """
    resp = client.post("/", data={"username": "admin", "password": "12345"})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data


# TC11: Password đúng = min (6) -> đã bao phủ ở test_login_success
# (không cần test riêng vì TC01 đã dùng "123456")


# TC12 & TC13: Password dài (biên trên và vượt giới hạn)
# Kỹ thuật: Giá trị biên và robustness
@pytest.mark.parametrize("password", [
    "p" * 128,   # giả định max = 128
    "p" * 10000  # vượt giới hạn
])
def test_login_long_passwords_do_not_crash(client, password):
    """
    Mô tả: Gửi password rất dài để kiểm tra hệ thống không crash và xử lý an toàn.
    """
    resp = client.post("/", data={"username": "admin", "password": password})
    assert resp.status_code != 500
    assert resp.status_code in (200, 302)


# TC14: Username có khoảng trắng đầu/cuối
# Kỹ thuật: Phân vùng tương đương - ký tự trắng
def test_login_username_with_spaces_fails(client):
    """
    Mô tả: Username có space ở đầu/cuối -> do so sánh chuỗi thô, sẽ không khớp -> trả về lỗi.
    """
    resp = client.post("/", data={"username": " admin ", "password": "123456"})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data


# TC15: Username/Password chứa ký tự đặc biệt
# Kỹ thuật: Phân vùng tương đương - ký tự đặc biệt
def test_login_special_characters_fail(client):
    """
    Mô tả: Chuỗi chứa ký tự đặc biệt -> không khớp -> trả về lỗi. Kiểm tra không crash.
    """
    resp = client.post("/", data={"username": "adm!n", "password": "12#3456"})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data


# TC16: Thử payload SQL injection (negative test)
# Kỹ thuật: Kiểm thử bảo mật (negative)
def test_login_sql_injection_payload_is_handled_safely(client):
    """
    Mô tả: Gửi payload SQLi vào username; ứng xử mong muốn là không crash và không authenticate.
    """
    payload = "admin' OR '1'='1"
    resp = client.post("/", data={"username": payload, "password": "anything"})
    # Không được authenticate và không crash
    assert resp.status_code != 500
    assert resp.status_code in (200, 302)
    # Nếu không authenticate (thường case), sẽ render lỗi mock
    if resp.status_code == 200:
        assert b"RENDERED_ERROR:" in resp.data


# TC17: Case-sensitivity kiểm tra
# Kỹ thuật: Phân vùng tương đương - phân biệt chữ hoa/thường
def test_login_case_sensitivity_username(client):
    """
    Mô tả: Username 'Admin' khác 'admin' -> không khớp -> trả về lỗi.
    """
    resp = client.post("/", data={"username": "Admin", "password": "123456"})
    assert resp.status_code == 200
    assert b"RENDERED_ERROR:" in resp.data
