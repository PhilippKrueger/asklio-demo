// Brutalist stats card component

interface StatsCardProps {
  label: string;
  value: string | number;
  mono?: boolean;
}

export default function StatsCard({ label, value, mono = true }: StatsCardProps) {
  return (
    <div className="border-3 border-black p-6">
      <div className="text-sm mb-2 opacity-60">{label}</div>
      <div className={`text-4xl font-bold ${mono ? 'font-mono' : ''}`}>
        {value}
      </div>
    </div>
  );
}
