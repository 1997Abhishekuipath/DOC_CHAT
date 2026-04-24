import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UploadSimple, FilePdf, FileDoc, FileText } from "@phosphor-icons/react";
import { toast } from "sonner";
import api from "@/lib/api";

export default function UploadDialog({ open, onOpenChange, onUploaded }) {
    const [file, setFile] = useState(null);
    const [tags, setTags] = useState("");
    const [busy, setBusy] = useState(false);

    const reset = () => { setFile(null); setTags(""); };
    const handleClose = (o) => { if (!o) reset(); onOpenChange(o); };

    const submit = async () => {
        if (!file) { toast.error("Choose a file"); return; }
        setBusy(true);
        try {
            const fd = new FormData();
            fd.append("file", file);
            fd.append("tags", tags);
            await api.post("/v2/documents/ingest", fd, { headers: { "Content-Type": "multipart/form-data" } });
            toast.success("Upload started — indexing in background");
            reset();
            onOpenChange(false);
            onUploaded?.();
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Upload failed");
        } finally {
            setBusy(false);
        }
    };

    const ext = file ? file.name.split(".").pop().toLowerCase() : "";
    const Icon = ext === "pdf" ? FilePdf : (ext === "docx" ? FileDoc : FileText);

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent data-testid="upload-dialog">
                <DialogHeader>
                    <DialogTitle className="font-heading text-2xl">Ingest Document</DialogTitle>
                    <DialogDescription>
                        Supported: PDF, DOCX, TXT, MD. Processing runs in the background.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    <label
                        htmlFor="file-input"
                        className="flex flex-col items-center justify-center border-2 border-dashed border-border hover:border-brand-primary transition-colors p-10 cursor-pointer"
                        data-testid="upload-dropzone"
                    >
                        {file ? (
                            <>
                                <Icon size={36} className="text-brand-primary" weight="duotone" />
                                <div className="mt-3 font-medium">{file.name}</div>
                                <div className="text-xs text-muted-foreground mt-1">
                                    {(file.size / 1024).toFixed(1)} KB
                                </div>
                            </>
                        ) : (
                            <>
                                <UploadSimple size={36} className="text-muted-foreground" weight="duotone" />
                                <div className="mt-3 font-medium">Click to choose a file</div>
                                <div className="text-xs text-muted-foreground mt-1">PDF · DOCX · TXT · MD</div>
                            </>
                        )}
                        <input
                            id="file-input"
                            type="file"
                            accept=".pdf,.docx,.txt,.md"
                            className="hidden"
                            data-testid="upload-file-input"
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                        />
                    </label>

                    <div>
                        <Label htmlFor="tags" className="dc-overline">Tags (optional)</Label>
                        <Input
                            id="tags"
                            placeholder="legal, q4-2025, finance"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            className="mt-1"
                            data-testid="upload-tags-input"
                        />
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => handleClose(false)} data-testid="upload-cancel-button">Cancel</Button>
                    <Button onClick={submit} disabled={busy || !file} data-testid="upload-submit-button">
                        {busy ? "Uploading…" : "Ingest"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
