import api from "./api";
import type {
  CreateScheduleDto,
  ScheduledScan,
  UpdateScheduleDto,
} from "@/types/schedule";

class ScheduleService {
  async getSchedules(): Promise<ScheduledScan[]> {
    const { data } = await api.get<ScheduledScan[]>("/schedules");
    return data;
  }

  async createSchedule(dto: CreateScheduleDto): Promise<ScheduledScan> {
    const { data } = await api.post<ScheduledScan>("/schedules", dto);
    return data;
  }

  async updateSchedule(
    id: number,
    dto: UpdateScheduleDto
  ): Promise<ScheduledScan> {
    const { data } = await api.patch<ScheduledScan>(`/schedules/${id}`, dto);
    return data;
  }

  async runNow(id: number): Promise<ScheduledScan> {
    const { data } = await api.post<ScheduledScan>(`/schedules/${id}/run`);
    return data;
  }

  async deleteSchedule(id: number): Promise<void> {
    await api.delete(`/schedules/${id}`);
  }
}

const scheduleService = new ScheduleService();

export default scheduleService;
