INSERT INTO knowledge_documents (title, content, content_summary, document_type, role_type)
    VALUES 
    (
        N'Hướng dẫn đăng ký môn học',
        N'Sinh viên đăng ký môn học qua hệ thống online trong thời gian từ 01/01 đến 07/01 mỗi học kỳ. Vào menu Đăng ký môn học > Chọn môn > Xác nhận.',
        N'Hướng dẫn đăng ký môn học cho sinh viên',
        'guide',
        'student'
    ),
    (
        N'Quy định về điểm số',
        N'Điểm số gồm: Chuyên cần (10%), Giữa kỳ (30%), Cuối kỳ (60%). Điểm tổng kết = 0.1*CC + 0.3*GK + 0.6*CK. Điểm đạt từ 4.0 trở lên.',
        N'Quy định tính điểm và điều kiện đạt môn',
        'regulation',
        'student'
    ),
    (
        N'Cách nhập điểm cho sinh viên',
        N'Giảng viên truy cập menu Quản lý điểm > Chọn lớp > Nhập điểm chuyên cần, giữa kỳ, cuối kỳ > Gửi duyệt cho admin.',
        N'Hướng dẫn nhập điểm cho giảng viên',
        'guide',
        'instructor'
    ),
    (
        N'Hướng dẫn tra cứu học phí',
        N'Sinh viên xem học phí tại menu Tài chính > Học phí. Hiển thị học phí theo học kỳ, số tiền còn nợ, hạn thanh toán.',
        N'Hướng dẫn tra cứu học phí',
        'guide',
        'student'
    );


INSERT INTO knowledge_documents (title, content, content_summary, document_type, role_type)
VALUES 
    (N'Hướng dẫn đăng ký môn học', 
    N'Để đăng ký môn học, sinh viên cần:
    1. Đăng nhập vào hệ thống bằng MSSV và mật khẩu
    2. Vào menu "Đăng ký môn học"
    3. Chọn học kỳ muốn đăng ký
    4. Tìm kiếm môn học theo mã môn hoặc tên môn
    5. Kiểm tra điều kiện tiên quyết (nếu có)
    6. Chọn lớp học phù hợp (kiểm tra lịch học, số chỗ trống)
    7. Nhấn "Thêm vào giỏ"
    8. Xem lại danh sách môn đã chọn
    9. Nhấn "Xác nhận đăng ký"
    10. Kiểm tra email xác nhận

    Lưu ý:
    - Thời gian đăng ký: Thường mở 1 tuần trước khi bắt đầu học kỳ
    - Số tín chỉ tối đa: 24 tín chỉ/học kỳ (sinh viên xuất sắc có thể đăng ký 28)
    - Số tín chỉ tối thiểu: 12 tín chỉ/học kỳ
    - Nếu lớp đầy, có thể đăng ký vào danh sách chờ', 
    N'Hướng dẫn chi tiết quy trình đăng ký môn học cho sinh viên, bao gồm các bước thực hiện và quy định về số tín chỉ',
    'guide', 'student'),

    (N'Quy định về điểm danh và vắng mặt',
    N'Quy định điểm danh:
    - Sinh viên phải có mặt đúng giờ quy định
    - Điểm danh được thực hiện trong 15 phút đầu tiên của buổi học
    - Đến muộn quá 15 phút: Vắng mặt không phép

    Quy định vắng mặt:
    - Tổng số buổi vắng không quá 20% tổng số buổi học (khoảng 3 buổi/môn)
    - Vượt quá 20%: Không được dự thi cuối kỳ, điểm F
    - Vắng có phép: Phải có giấy xác nhận (bệnh viện, gia đình...)
    - Nộp đơn xin phép vắng trước hoặc trong 3 ngày sau khi vắng

    Hậu quả:
    - Vắng 4+ buổi: Cấm thi, điểm F
    - Vắng thi giữa kỳ không phép: Điểm 0
    - Vắng thi cuối kỳ không phép: Điểm F môn học',
    N'Quy định về điểm danh, vắng mặt và các hậu quả khi vi phạm quy định',
    'regulation', 'student'),

    (N'Hướng dẫn tra cứu điểm thi',
    N'Cách tra cứu điểm:
    1. Đăng nhập hệ thống
    2. Vào menu "Kết quả học tập"
    3. Chọn học kỳ cần xem
    4. Xem điểm từng môn học (điểm thành phần, điểm tổng kết)
    5. Xem GPA học kỳ và GPA tích lũy

    Thành phần điểm:
    - Điểm chuyên cần: 10%
    - Điểm giữa kỳ: 30%
    - Điểm cuối kỳ: 60%
    - Điểm tổng kết = (CC*0.1 + GK*0.3 + CK*0.6)

    Thang điểm:
    - A: 8.5 - 10
    - B+: 8.0 - 8.4
    - B: 7.0 - 7.9
    - C+: 6.5 - 6.9
    - C: 5.5 - 6.4
    - D+: 5.0 - 5.4
    - D: 4.0 - 4.9
    - F: < 4.0 (Không đạt)

    Phúc khảo điểm:
    - Thời gian: Trong 7 ngày sau khi công bố điểm
    - Nộp đơn tại phòng Đào tạo
    - Lệ phí: 50,000 VNĐ/môn',
    N'Hướng dẫn tra cứu điểm thi, thang điểm và quy trình phúc khảo',
    'guide', 'student'),

    (N'Quy định về học phí và miễn giảm',
    N'Học phí:
    - Học phí tính theo tín chỉ
    - Mức phí: 350,000 VNĐ/tín chỉ (khối ngành kỹ thuật)
    - Mức phí: 280,000 VNĐ/tín chỉ (khối ngành kinh tế)
    - Học lại: Tính theo mức phí hiện hành

    Thời hạn đóng học phí:
    - Đợt 1: Trong 2 tuần đầu học kỳ
    - Đợt 2: Trước khi thi giữa kỳ (nếu chưa đóng đợt 1)
    - Trễ hạn: Phạt 5%/tháng

    Miễn giảm học phí:
    - Sinh viên diện chính sách: Giảm 50-100%
    - Sinh viên dân tộc thiểu số: Giảm 30%
    - Sinh viên có hoàn cảnh khó khăn: Xét hỗ trợ từng trường hợp
    - Sinh viên đạt thành tích xuất sắc: Giảm 20-50%

    Hồ sơ xét miễn giảm:
    1. Đơn xin miễn giảm
    2. Giấy xác nhận hộ khẩu/thu nhập
    3. Bản sao chứng chỉ (nếu có)
    4. Nộp tại phòng Công tác sinh viên trước 15/8 (kỳ 1) hoặc 15/1 (kỳ 2)',
    N'Quy định về mức học phí, thời hạn đóng và các chính sách miễn giảm học phí',
    'regulation', 'student'),

    (N'Thủ tục xin nghỉ học và bảo lưu',
    N'Nghỉ học tạm thời (bảo lưu):
    - Thời gian tối đa: 2 học kỳ liên tục hoặc 3 học kỳ không liên tục
    - Lý do được chấp nhận: Sức khỏe, gia đình, nghĩa vụ quân sự
    - Nộp đơn trước 2 tuần kể từ ngày khai giảng

    Hồ sơ bảo lưu:
    1. Đơn xin bảo lưu (có xác nhận của gia đình)
    2. Giấy xác nhận lý do (bệnh viện, địa phương...)
    3. Nộp tại phòng Đào tạo
    4. Chờ phê duyệt (3-5 ngày làm việc)

    Thủ tục quay lại học:
    - Nộp đơn xin quay lại học trước 1 tuần kể từ ngày khai giảng
    - Đóng học phí đúng hạn
    - Đăng ký môn học theo quy định

    Thôi học:
    - Nộp đơn thôi học + Biên nhận đã trả sách thư viện
    - Nộp thẻ sinh viên
    - Nhận giấy xác nhận thôi học sau 7 ngày
    - Không được hoàn học phí đã đóng',
    N'Quy trình và thủ tục xin nghỉ học tạm thời, bảo lưu và thôi học',
    'regulation', 'student'),

    (N'Hướng dẫn đăng ký học lại môn thi hỏng',
    N'Học lại môn F:
    - Sinh viên phải đăng ký học lại môn có điểm F
    - Đăng ký vào học kỳ tiếp theo hoặc học kỳ hè
    - Học phí tính theo mức hiện hành
    - Điểm cũ bị ghi đè bởi điểm mới

    Học cải thiện điểm:
    - Chỉ áp dụng cho môn có điểm D, D+, C
    - Tối đa 3 môn/năm học
    - Tính điểm cao hơn (nếu điểm mới cao hơn)
    - Lệ phí: 200,000 VNĐ/môn

    Lưu ý:
    - Ưu tiên đăng ký môn học lại trước môn học mới
    - Kiểm tra lịch học tránh trùng giờ
    - Nếu môn học bị hủy, sẽ được hoàn học phí
    - Môn tiên quyết phải PASS trước khi học môn tiếp theo',
    N'Hướng dẫn đăng ký học lại môn thi hỏng và học cải thiện điểm',
    'guide', 'student'),

    (N'Quy định cấp bằng tốt nghiệp',
    N'Điều kiện tốt nghiệp:
    - Hoàn thành đủ số tín chỉ theo chương trình (tối thiểu 120-140 tín chỉ)
    - GPA tích lũy >= 2.0
    - Không môn nào điểm F
    - Hoàn thành khóa luận/đồ án tốt nghiệp (>= 5.0)
    - Đạt chuẩn ngoại ngữ đầu ra (TOEIC >= 450 hoặc tương đương)
    - Không vi phạm quy chế sinh viên nghiêm trọng

    Thời gian cấp bằng:
    - Xét tốt nghiệp: Tháng 6 và tháng 12 hàng năm
    - Nhận bằng: Sau 3-6 tháng kể từ ngày xét tốt nghiệp
    - Nhận bằng tạm thời: Ngay sau lễ tốt nghiệp

    Xếp loại tốt nghiệp:
    - Xuất sắc: GPA >= 3.6, không môn nào dưới B
    - Giỏi: GPA >= 3.2
    - Khá: GPA >= 2.5
    - Trung bình: GPA >= 2.0

    Lưu ý:
    - Bằng gốc chỉ cấp 1 lần duy nhất
    - Nếu mất, chỉ cấp bản sao có giá trị pháp lý
    - Lệ phí làm lại: 500,000 VNĐ',
    N'Điều kiện tốt nghiệp, xếp loại bằng và thủ tục cấp bằng tốt nghiệp',
    'regulation', 'student'),

    (N'Hướng dẫn đăng ký lịch thi cuối kỳ',
    N'Quy trình đăng ký lịch thi:
    1. Hệ thống tự động xếp lịch thi cho các môn đã đăng ký
    2. Kiểm tra lịch thi qua menu "Lịch thi"
    3. Nếu trùng lịch: Nộp đơn xin thi vào lịch dự bị (trong 48h)
    4. In phiếu dự thi trước 3 ngày

    Quy định trong phòng thi:
    - Mang theo thẻ sinh viên + CMND/CCCD
    - Đến trước 15 phút, muộn quá 15 phút không được vào
    - Không mang tài liệu, điện thoại vào phòng thi (trừ môn cho phép)
    - Làm bài đúng giấy thi, viết bằng mực xanh hoặc đen
    - Nộp bài trước khi hết giờ, không được rời phòng sớm hơn 30 phút

    Vi phạm kỷ luật thi:
    - Quay cóp: Điểm 0, kỷ luật
    - Mang tài liệu không được phép: Điểm 0
    - Gây rối trật tự: Đình chỉ thi
    - Nhờ người thi hộ: Đình chỉ học, buộc thôi học',
    N'Quy trình đăng ký lịch thi cuối kỳ và quy định trong phòng thi',
    'guide', 'student');
