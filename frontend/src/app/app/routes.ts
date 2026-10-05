import { inject } from "@angular/core";
import { CanActivateFn, Router, Routes } from "@angular/router";
import { AuthService } from "../entities/user/auth.service";

const authenticated: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  try {
    await auth.restore();
    return true;
  } catch {
    return router.createUrlTree(["/login"]);
  }
};

export const routes: Routes = [
  {
    path: "login",
    loadComponent: () =>
      import("../pages/login/login.component").then((m) => m.LoginComponent),
  },

  {
    path: "leads",
    canActivate: [authenticated],
    loadComponent: () =>
      import("../pages/leads/leads.component").then((m) => m.LeadsComponent),
  },

  { path: "", redirectTo: "leads", pathMatch: "full" },

  { path: "**", redirectTo: "leads" },
];
