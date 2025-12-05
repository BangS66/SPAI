import { cn } from "@/lib/utils";

const SpaiLogo = ({ className, ...props }: React.HTMLAttributes<SVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 100 28"
    className={cn("fill-current text-sidebar-primary", className)}
    {...props}
  >
    <text
      x="0"
      y="22"
      className="font-headline text-3xl font-bold"
      style={{
        fontFamily: 'Inter, sans-serif'
      }}
    >
      SPAI
    </text>
  </svg>
);

export default SpaiLogo;
