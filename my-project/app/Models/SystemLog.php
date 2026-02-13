<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class SystemLog extends Model
{
    protected $fillable = [
        'level',
        'message',
        'exception',
        'trace',
        'url',
        'method',
        'ip',
        'user_id',
        'user_agent',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}
