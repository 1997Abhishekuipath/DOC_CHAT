import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

export default function AdminUsers() {
    const [users, setUsers] = useState([]);

    const load = () => api.get("/admin/users").then((r) => setUsers(r.data)).catch(() => {});
    useEffect(() => { load(); }, []);

    const changeRole = async (userId, role) => {
        try {
            await api.patch(`/admin/users/${userId}`, { role });
            toast.success("Role updated");
            setUsers((c) => c.map((u) => (u.id === userId ? { ...u, role } : u)));
        } catch (e) {
            toast.error("Update failed");
        }
    };

    return (
        <div>
            <header className="h-16 border-b border-border px-8 flex items-center sticky top-0 bg-background z-10">
                <div>
                    <div className="dc-overline">Admin</div>
                    <h1 className="font-heading font-bold text-lg">Users</h1>
                </div>
            </header>
            <div className="p-8 max-w-5xl">
                <div className="border border-border">
                    <div className="grid grid-cols-[1fr_1fr_160px_180px] gap-4 px-4 py-3 bg-secondary/50 border-b border-border text-xs font-mono uppercase tracking-wider text-muted-foreground">
                        <div>Name</div>
                        <div>Email</div>
                        <div>Joined</div>
                        <div>Role</div>
                    </div>
                    {users.map((u) => (
                        <div key={u.id} className="grid grid-cols-[1fr_1fr_160px_180px] gap-4 px-4 py-3 border-b border-border last:border-b-0 items-center" data-testid={`user-row-${u.id}`}>
                            <div className="font-medium">{u.name}</div>
                            <div className="text-sm font-mono text-muted-foreground truncate">{u.email}</div>
                            <div className="text-xs font-mono text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</div>
                            <Select value={u.role} onValueChange={(v) => changeRole(u.id, v)}>
                                <SelectTrigger className="h-8 text-xs" data-testid={`role-select-${u.id}`}>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="owner">Owner</SelectItem>
                                    <SelectItem value="editor">Editor</SelectItem>
                                    <SelectItem value="viewer">Viewer</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
