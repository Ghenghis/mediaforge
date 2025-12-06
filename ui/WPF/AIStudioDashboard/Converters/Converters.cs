using System.Globalization;
using System.Windows;
using System.Windows.Data;
using System.Windows.Media;

namespace AIStudioDashboard.Converters;

public class BoolToColorConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool isOnline)
        {
            return isOnline 
                ? new SolidColorBrush(Color.FromRgb(34, 197, 94))   // Green
                : new SolidColorBrush(Color.FromRgb(239, 68, 68));  // Red
        }
        return new SolidColorBrush(Color.FromRgb(100, 116, 139));   // Gray
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}

public class BoolToStatusConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool isOnline)
            return isOnline ? "ONLINE" : "OFFLINE";
        return "UNKNOWN";
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}

public class BoolToApprovalConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool approved)
            return approved ? "✓" : "✗";
        return "?";
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}

public class InverseBoolConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool b)
            return !b;
        return true;
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}

public class GradeToColorConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is string grade)
        {
            return grade switch
            {
                "S+" or "S" => new SolidColorBrush(Color.FromRgb(255, 215, 0)),   // Gold
                "A+" or "A" or "A-" => new SolidColorBrush(Color.FromRgb(34, 197, 94)),   // Green
                "B+" or "B" or "B-" => new SolidColorBrush(Color.FromRgb(59, 130, 246)),  // Blue
                "C+" or "C" or "C-" => new SolidColorBrush(Color.FromRgb(245, 158, 11)), // Amber
                _ => new SolidColorBrush(Color.FromRgb(100, 116, 139))  // Gray
            };
        }
        return new SolidColorBrush(Color.FromRgb(100, 116, 139));
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}

public class PercentageConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is double d)
            return $"{d:F0}%";
        return "0%";
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}

public class ModelColorConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is string name)
        {
            return name.ToUpper() switch
            {
                "BRONZE" => new SolidColorBrush(Color.FromRgb(205, 127, 50)),
                "SILVER" => new SolidColorBrush(Color.FromRgb(192, 192, 192)),
                "GOLD" => new SolidColorBrush(Color.FromRgb(255, 215, 0)),
                "PLATINUM" => new SolidColorBrush(Color.FromRgb(229, 228, 226)),
                _ => new SolidColorBrush(Color.FromRgb(148, 163, 184))
            };
        }
        return new SolidColorBrush(Color.FromRgb(148, 163, 184));
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}
