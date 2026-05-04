"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

interface Props {
  onSubmit: (content: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    onSubmit(text);
    setValue("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 rounded-md border bg-background p-2"
    >
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as unknown as React.FormEvent);
          }
        }}
        rows={2}
        disabled={disabled}
        placeholder="Ask about the dataset… (Enter to send, Shift+Enter for newline)"
        className="flex-1 resize-none bg-transparent p-2 text-sm outline-none disabled:opacity-50"
      />
      <Button type="submit" disabled={disabled || !value.trim()}>
        {disabled ? "Sending…" : "Send"}
      </Button>
    </form>
  );
}
