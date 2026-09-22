export interface TagInfo {
  title: string;
  artist: string;
  album: string;
  year: string;
  track: string;
}

export interface AudioFileInfo {
  file_path: string;
  mtime: number;
  file_size: number;
  md5_hash: string;
  duration: number;
  bitrate: number;
  sample_rate: number;
  is_lossless: number | boolean;
  channels: number;
  format: string;
  fingerprint: string;
  raw_title?: string;
  raw_artist?: string;
  raw_album?: string;
  raw_year?: string;
  raw_track?: string;
}

export interface KeeperAction {
  source: string;
  destination: string;
  old_tags: TagInfo;
  new_tags: TagInfo;
  file_info: AudioFileInfo;
}

export interface TrashAction {
  source: string;
  destination: string;
  reason: string;
  file_info: AudioFileInfo;
}

export interface ScanSummary {
  total_files: number;
  keepers_count: number;
  duplicates_count: number;
  trash_dir: string;
  dry_run: boolean;
}

export interface ScanResult {
  mode: "dry_run" | "applied";
  summary: ScanSummary;
  keepers: KeeperAction[];
  duplicates: TrashAction[];
  transliteration_count: number;
  elapsed_seconds: number;
  execution?: {
    session_id: string;
    moved_to_trash: any[];
    reorganized: any[];
    errors: string[];
  };
}

export interface SystemStatus {
  tools: {
    fpcalc: boolean;
    ffmpeg: boolean;
    python: boolean;
    openaiKeyConfigured: boolean;
  };
  testLibrary: {
    path: string;
    exists: boolean;
    fileCount: number;
  };
}
