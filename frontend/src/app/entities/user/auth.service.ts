import { Injectable, inject, signal } from "@angular/core";
import { ApiService } from "../../shared/api/api.service";
export interface User {
  id: number;
  username: string;
}
@Injectable({ providedIn: "root" })
export class AuthService {
  private api = inject(ApiService);
  user = signal<User | null>(null);
  async restore() {
    this.user.set(await this.api.request<User>("auth/me/"));
  }
  async login(username: string, password: string) {
    await this.api.request("auth/csrf/");
    this.user.set(
      await this.api.request<User>("auth/login/", "POST", {
        username,
        password,
      }),
    );
  }
  async logout() {
    await this.api.request("auth/logout/", "POST");
    this.user.set(null);
  }
}
