import SpaiLogo from "@/components/icons/spai-logo";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Instagram } from "lucide-react";
import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="flex flex-1 items-center justify-center p-4 sm:p-6 md:p-8">
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="items-center text-center">
          <SpaiLogo className="w-24 h-auto text-primary mb-4" />
          <CardTitle className="text-2xl font-bold tracking-tight">
            SPAI: Smart Photo AI
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
            <p className="text-muted-foreground">
                An intelligent application to sort, select, and rate photos using Artificial Intelligence.
            </p>
            <div className="flex items-center justify-center gap-4 pt-4">
                <p className="font-semibold">Created by:</p>
                <Link
                    href="https://www.instagram.com/wawansft"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-accent-foreground/80 hover:text-accent-foreground hover:underline transition-colors"
                >
                    <Instagram className="h-5 w-5 text-primary" />
                    <span>@wawansft</span>
                </Link>
            </div>
        </CardContent>
      </Card>
    </div>
  );
}
