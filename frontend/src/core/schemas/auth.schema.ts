import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(3, "Tên đăng nhập phải chứa ít nhất 3 ký tự."),
  password: z.string().min(6, "Mật khẩu quá ngắn."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = loginSchema.extend({
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Mật khẩu xác nhận không khớp.",
  path: ["confirmPassword"],
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
