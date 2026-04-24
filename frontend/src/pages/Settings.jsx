import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle } from "@phosphor-icons/react";

export default function Settings() {
    const { user } = useAuth();
    const [flags, setFlags] = useState({});
    const [providers, setProviders] = useState(null);

    useEffect(() => {
        api.get("/v2/flags").then((r) => setFlags(r.data)).catch(() => {});
        api.get("/v2/providers").then((r) => setProviders(r.data)).catch(() => {});
    }, []);

    return (
        <div>
            <header className="h-16 border-b border-border px-8 flex items-center sticky top-0 bg-background z-10">
                <div>
                    <div className="dc-overline">Account</div>
                    <h1 className="font-heading font-bold text-lg">Settings</h1>
                </div>
            </header>
            <div className="p-8 max-w-4xl space-y-8">
                <section>
                    <div className="dc-overline mb-3">Profile</div>
                    <div className="border border-border p-6 grid md:grid-cols-3 gap-4">
                        <div>
                            <div className="text-xs text-muted-foreground">Name</div>
                            <div className="font-medium mt-1" data-testid="settings-name">{user?.name}</div>
                        </div>
                        <div>
                            <div className="text-xs text-muted-foreground">Email</div>
                            <div className="font-mono text-sm mt-1" data-testid="settings-email">{user?.email}</div>
                        </div>
                        <div>
                            <div className="text-xs text-muted-foreground">Role</div>
                            <div className="mt-1"><Badge className="font-mono uppercase" data-testid="settings-role">{user?.role}</Badge></div>
                        </div>
                    </div>
                </section>

                <section>
                    <div className="dc-overline mb-3">Active providers</div>
                    <p className="text-xs text-muted-foreground mb-4">Runtime-switchable via <span className="dc-kbd">LLM_PROVIDER</span> and <span className="dc-kbd">EMBEDDING_PROVIDER</span> env vars.</p>
                    {providers && (
                        <div className="grid md:grid-cols-2 gap-0 border-l border-t border-border">
                            <div className="border-r border-b border-border p-6" data-testid="provider-llm">
                                <div className="dc-overline mb-2">LLM (chat)</div>
                                <div className="font-heading font-bold text-2xl">{providers.llm.provider}</div>
                                <div className="text-xs font-mono text-muted-foreground mt-1">{providers.llm.model}</div>
                            </div>
                            <div className="border-r border-b border-border p-6" data-testid="provider-embedding">
                                <div className="dc-overline mb-2">Embeddings</div>
                                <div className="font-heading font-bold text-2xl">{providers.embedding.provider}</div>
                                <div className="text-xs font-mono text-muted-foreground mt-1">{providers.embedding.model}</div>
                            </div>
                        </div>
                    )}
                </section>

                <section>
                    <div className="dc-overline mb-3">Feature flags</div>
                    <p className="text-xs text-muted-foreground mb-4">Toggled server-side via env vars. Read-only view.</p>
                    <div className="border border-border">
                        {Object.entries(flags).map(([k, v], i) => (
                            <div
                                key={k}
                                className={`grid grid-cols-[1fr_100px] items-center px-4 py-2.5 ${i < Object.keys(flags).length - 1 ? "border-b border-border" : ""}`}
                                data-testid={`flag-row-${k}`}
                            >
                                <div className="font-mono text-[13px]">{k}</div>
                                <div className="flex items-center gap-1.5 text-xs font-mono justify-end">
                                    {v ? (
                                        <span className="text-confidence-high flex items-center gap-1"><CheckCircle size={14} weight="fill" /> ON</span>
                                    ) : (
                                        <span className="text-muted-foreground flex items-center gap-1"><XCircle size={14} weight="fill" /> OFF</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
}
