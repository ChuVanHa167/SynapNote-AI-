import { MeetingSummary, MeetingDetail } from '@/types/meeting';

export const mockMeetingsList: MeetingSummary[] = [
    { id: "synap-workshop", name: "Đồng bộ chiến lược Marketing Q4", date: "Hôm nay, 10:30 AM", duration: "45m 20s", status: "HOÀN THÀNH", statusColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20", participants: 4 },
    { id: "product-sync", name: "Product Sync: Tính năng mới", date: "Hôm qua, 14:00 PM", duration: "32m 10s", status: "HOÀN THÀNH", statusColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20", participants: 3 },
    { id: "client-pitch", name: "Pitching Khách hàng ABC", date: "24 Thg 10, 09:00 AM", duration: "1h 15m", status: "ĐANG XỬ LÝ", statusColor: "text-amber-500 bg-amber-500/10 border-amber-500/20", participants: 5 },
    { id: "design-review", name: "Review thiết kế UI/UX v2.0", date: "22 Thg 10, 15:30 PM", duration: "50m 00s", status: "HOÀN THÀNH", statusColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20", participants: 2 },
    { id: "weekly-standup", name: "Weekly Standup Đội Dev", date: "20 Thg 10, 10:00 AM", duration: "1s 20m", status: "HOÀN THÀNH", statusColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20", participants: 8 },
];

export const mockMeetingDetail: MeetingDetail = {
    id: "synap-workshop",
    title: "Đồng bộ chiến lược Marketing Q4",
    date: "26 Thg 10, 2023",
    duration: "45:20",
    summary: "Cuộc họp tập trung vào việc chốt ngân sách cho Q4. Đội ngũ đồng ý chuyển 20% ngân sách dư từ Q3 sang cho marketing hiệu suất (performance marketing). Vẫn còn một số lo ngại về việc chậm trễ tiến độ hình ảnh, cần được xử lý ngay lập tức.",
    actionItems: [
        { id: "1", task: "Chốt duyệt lại tiến độ thiết kế hình ảnh", assignee: "Sarah", deadline: "28/10", status: "pending" },
        { id: "2", task: "Phê duyệt phân bổ lại ngân sách Q4", assignee: "Michael", deadline: "Hoàn thành", status: "completed" }
    ],
    decisions: [
        "Tăng 20% ngân sách cho marketing hiệu suất.",
        "Thuê thêm hai designer làm freelance để giải quyết tình trạng kẹt việc thiết kế."
    ],
    transcript: [
        { id: "1", time: "00:00", seconds: 0, speaker: "Michael", text: "Được rồi, chúng ta bắt đầu nhé. Mục tiêu chính hôm nay là chốt ngân sách Q4 và giải quyết vấn đề chậm trễ thiết kế." },
        { id: "2", time: "00:15", seconds: 15, speaker: "Sarah", text: "Trước khi bàn về con số, tôi muốn lưu ý rằng đội thiết kế hiện tại đã làm việc với 120% công suất." },
        { id: "3", time: "00:30", seconds: 30, speaker: "David", text: "Đã hiểu. Nếu chúng ta chuyển một phần tiền dư từ Q3 sang marketing hiệu suất, chúng ta có thể trích một khoản để thuê freelance không?" },
        { id: "4", time: "01:10", seconds: 70, speaker: "Michael", text: "Nghe hợp lý. Hãy cố gắng tuyển hai bạn freelance vào tuần tới. Sarah, bạn có thể phụ trách việc này không?" },
        { id: "5", time: "01:45", seconds: 105, speaker: "Sarah", text: "Vâng, tôi sẽ bắt đầu quy trình phỏng vấn ngay lập tức." },
    ]
};
