export type ScheduleCadence = "DAILY" | "WEEKLY" | "MONTHLY";

export type ScheduleWeekDay =
  | "MON"
  | "TUE"
  | "WED"
  | "THU"
  | "FRI"
  | "SAT"
  | "SUN";

export interface ScheduledScan {
  id: number;
  asset_id: number;
  asset_name: string | null;
  scanner: string;
  cadence: ScheduleCadence;
  time_of_day: string;
  week_day: ScheduleWeekDay | null;
  month_day: number | null;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface CreateScheduleDto {
  asset_id: number;
  cadence: ScheduleCadence;
  time_of_day: string;
  week_day?: ScheduleWeekDay | null;
  month_day?: number | null;
  scanner?: string;
  enabled?: boolean;
}

export type UpdateScheduleDto = Partial<CreateScheduleDto>;
