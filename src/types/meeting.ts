export interface TranscriptLine {
    id: number;
    time: string;
    seconds: number;
    speaker: string;
    text: string;
}

export interface ActionItem {
    id: number;
    task: string;
    assignee: string;
    deadline: string;
    status: 'pending' | 'completed';
}

export interface MeetingDetail {
    id: string;
    title: string;
    date: string;
    duration: string;
    summary: string;
    actionItems: ActionItem[];
    decisions: string[];
    transcript: TranscriptLine[];
}

export interface MeetingSummary {
    id: string;
    name: string;
    date: string;
    duration: string;
    status: string;
    statusColor: string;
    participants: number;
}
