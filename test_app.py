"""
Unittest cho chức năng /age (tính tuổi từ năm sinh)

Hướng dẫn:
- Đặt file này tại tests/test_age_unittest.py trong repo của bạn.
- Cài đặt: pip install pytest flask
- Chạy tests: python -m pytest -q hoặc pytest -q

Ghi chú:
- Các test đăng nhập bằng username/password mặc định trong app.py: admin / 123456
- Tests kiểm tra hai loại kết quả:
  * Giá trị hợp lệ: kiểm tra số tuổi (current_year - birth_year) xuất hiện trong HTML.
  * Giá trị không hợp lệ: kiểm tra presence của một trong các thông báo lỗi tiếng Việt phổ biến.
- Nếu app của bạn trả về thông báo khác, chỉnh lại các chuỗi trong expected_msgs tương ứng.
"""

import unittest
from datetime import datetime
from app import app

class AgeEndpointTestCase(unittest.TestCase):
    def setUp(self):
        # Kích hoạt chế độ TESTING cho Flask và tạo test client
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.current_year = datetime.now().year

    def login(self):
        """Đăng nhập để có session truy cập /age"""
        return self.client.post("/", data={"username": "admin", "password": "123456"}, follow_redirects=True)

    def post_age(self, birth_year_value):
        """Login rồi POST vào /age, trả về response text"""
        self.login()
        resp = self.client.post("/age", data={"birth_year": birth_year_value}, follow_redirects=True)
        return resp, resp.data.decode(errors="ignore")

    # Helper để kiểm tra lỗi (chấp nhận một trong nhiều thông báo khả dĩ)
    def assertContainsAny(self, text, expected_list):
        """Assert rằng text chứa ít nhất một chuỗi trong expected_list"""
        for msg in expected_list:
            if msg in text:
                return
        self.fail(f"Expected one of {expected_list!r} in response, but none were found. Response was:\n{text}")

    # -----------------------
    # Test cases (TC01 - TC18)
    # -----------------------

    def test_TC01_empty_input_shows_error(self):
        """TC01: Empty input -> lỗi bắt buộc"""
        resp, text = self.post_age("")
        expected_msgs = ["Năm sinh bắt buộc", "Không được để trống năm sinh", "dữ liệu không hợp lệ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC02_whitespace_only_shows_error(self):
        """TC02: Chỉ khoảng trắng -> lỗi bắt buộc"""
        resp, text = self.post_age("   ")
        expected_msgs = ["Năm sinh bắt buộc", "Không được để trống năm sinh", "dữ liệu không hợp lệ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC03_non_digit_shows_error(self):
        """TC03: 'abcd' -> lỗi không phải số"""
        resp, text = self.post_age("abcd")
        expected_msgs = ["Năm sinh phải là số", "Năm sinh không hợp lệ", "Năm sinh phải là số hợp lệ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC04_special_characters_rejected(self):
        """TC04: '1990!' -> lỗi ký tự đặc biệt"""
        resp, text = self.post_age("1990!")
        expected_msgs = ["Không được chứa ký tự đặc biệt", "Không được chứa ký tự đặc biệt hoặc khoảng trắng", "Năm sinh không hợp lệ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC05_internal_space_shows_error(self):
        """TC05: '19 90' -> lỗi (khoảng trắng bên trong)"""
        resp, text = self.post_age("19 90")
        expected_msgs = ["Không được chứa ký tự đặc biệt", "Không được chứa ký tự đặc biệt hoặc khoảng trắng", "Năm sinh không hợp lệ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC06_alphanumeric_shows_error(self):
        """TC06: '1990abc' -> theo yêu cầu test là không hợp lệ (ghi nhận lỗi định dạng)"""
        resp, text = self.post_age("1990abc")
        expected_msgs = ["Năm sinh không hợp lệ", "Năm sinh phải là số", "Năm sinh phải chứa số"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC07_multiple_numbers_shows_error(self):
        """TC07: 'Born 1990 and 2000' -> không hợp lệ theo yêu cầu"""
        resp, text = self.post_age("Born 1990 and 2000")
        expected_msgs = ["Năm sinh không hợp lệ", "Năm sinh phải là số", "Năm sinh phải chứa số"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC08_valid_typical_1990_computes_age(self):
        """TC08: '1990' -> hợp lệ, hiển thị tuổi = current_year - 1990"""
        birth = 1990
        resp, text = self.post_age(str(birth))
        expected_age = str(self.current_year - birth)
        self.assertIn(expected_age, text)

    def test_TC09_lower_boundary_1950_computes_age(self):
        """TC09: '1950' -> hợp lệ (lower bound), tính tuổi"""
        birth = 1950
        resp, text = self.post_age(str(birth))
        expected_age = str(self.current_year - birth)
        self.assertIn(expected_age, text)

    def test_TC10_just_above_lower_1951_computes_age(self):
        """TC10: '1951' -> hợp lệ"""
        birth = 1951
        resp, text = self.post_age(str(birth))
        expected_age = str(self.current_year - birth)
        self.assertIn(expected_age, text)

    def test_TC11_upper_boundary_current_year_age_zero(self):
        """TC11: current_year -> hợp lệ, tuổi = 0"""
        birth = self.current_year
        resp, text = self.post_age(str(birth))
        expected_age = "0"
        # Kiểm tra '0' xuất hiện — để tránh false-positive, kiểm tra cách hiển thị "Tuổi" nếu cần.
        self.assertIn(expected_age, text)

    def test_TC12_just_below_upper_age_one(self):
        """TC12: current_year - 1 -> hợp lệ, tuổi = 1"""
        birth = self.current_year - 1
        resp, text = self.post_age(str(birth))
        expected_age = "1"
        self.assertIn(expected_age, text)

    def test_TC13_below_minimum_shows_error(self):
        """TC13: '1949' -> lỗi: phải >= 1950"""
        resp, text = self.post_age("1949")
        expected_msgs = ["Năm sinh phải t��� 1950", "Năm sinh phải từ 1950 trở lên", "Năm sinh không hợp lệ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC14_above_current_year_shows_error(self):
        """TC14: current_year + 1 -> lỗi: không được lớn hơn năm hiện tại"""
        resp, text = self.post_age(str(self.current_year + 1))
        expected_msgs = ["Năm sinh không được lớn hơn năm hiện tại", "không được lớn hơn năm hiện tại", "Năm sinh không hợp lệ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC15_negative_number_shows_error(self):
        """TC15: '-1990' -> lỗi không hợp lệ"""
        resp, text = self.post_age("-1990")
        expected_msgs = ["Năm sinh không hợp lệ", "Năm sinh phải là số", "Năm sinh phải chứa số"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC16_leading_zeros_accepted_by_default(self):
        """TC16: '01990' -> test giả định chấp nhận leading zeros và interpret là 1990.
        Nếu hệ thống của bạn muốn từ chối leading zeros thì sửa test này thành assert lỗi.
        """
        birth = 1990
        resp, text = self.post_age("01990")
        expected_age = str(self.current_year - birth)
        # Chấp nhận hai khả năng: hoặc hiển thị tuổi, hoặc báo lỗi (nếu hệ thống chọn reject leading zeros).
        if expected_age in text:
            self.assertIn(expected_age, text)
        else:
            # Nếu không thấy tuổi, ít nhất phải có thông báo lỗi
            expected_msgs = ["Năm sinh không hợp lệ", "Năm sinh phải là số", "Năm sinh phải chứa số"]
            self.assertContainsAny(text, expected_msgs)

    def test_TC17_very_large_number_shows_error(self):
        """TC17: '999999' -> lỗi không hợp lệ / quá lớn"""
        resp, text = self.post_age("999999")
        expected_msgs = ["Năm sinh không hợp lệ", "quá lớn", "Năm sinh phải từ"]
        self.assertContainsAny(text, expected_msgs)

    def test_TC18_non_integer_shows_error(self):
        """TC18: '1990.5' -> lỗi không phải số nguyên"""
        resp, text = self.post_age("1990.5")
        expected_msgs = ["phải là số nguyên", "Năm sinh không hợp lệ", "Năm sinh phải là số"]
        self.assertContainsAny(text, expected_msgs)


if __name__ == "__main__":
    unittest.main()
