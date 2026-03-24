import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const CHART_COLORS = ['#c89b3c', '#0397ab', '#e44040', '#3bbf9e', '#9d48e0', '#576bce'];

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2">
      {payload.map((entry, index) => (
        <p key={index} className="text-sm text-gray-200">
          <span style={{ color: entry.color || entry.fill }}>{entry.name}: </span>
          <span className="font-semibold">{entry.value}</span>
        </p>
      ))}
    </div>
  );
};

export function PieChartWidget({ data, width = 200, height = 200, innerRadius = 40, outerRadius = 70 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          dataKey="value"
          strokeWidth={2}
          stroke="#0a0e1a"
        >
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.color || CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function BarChartWidget({
  data,
  dataKey = 'value',
  xAxisKey = 'name',
  height = 200,
  barColor = '#c89b3c',
  layout = 'vertical',
  customTooltip,
}) {
  if (layout === 'vertical') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
          <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} domain={[0, 'auto']} />
          <YAxis
            dataKey={xAxisKey}
            type="category"
            tick={{ fill: '#d1d5db', fontSize: 11 }}
            width={50}
            interval={0}
          />
          <Tooltip content={customTooltip || <CustomTooltip />} />
          <Bar dataKey={dataKey} fill={barColor} radius={[0, 4, 4, 0]} barSize={14} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis dataKey={xAxisKey} tick={{ fill: '#9ca3af', fontSize: 12 }} />
        <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey={dataKey} fill={barColor} radius={[4, 4, 0, 0]} barSize={28} />
      </BarChart>
    </ResponsiveContainer>
  );
}
