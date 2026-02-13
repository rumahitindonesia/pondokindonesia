<?php
$file = '/home/triyono/my-project/storage/logs/laravel.log';
if (!file_exists($file)) {
    echo "Log file not found.\n";
    exit;
}
$content = file_get_contents($file);
$lines = explode("\n", $content);
$lastLines = array_slice($lines, -200); // Last 200 lines to be safe
foreach ($lastLines as $line) {
    if (strpos($line, 'production.ERROR') !== false || strpos($line, 'local.ERROR') !== false) {
        // Extract date to verify recentness
        preg_match('/^\[(.*?)\]/', $line, $matches);
        $date = $matches[1] ?? 'Unknown';
        
        // Extract message (up to the JSON part or first 500 chars)
        $message = substr($line, 0, 500);
        echo "[$date] $message\n---\n";
    }
}
