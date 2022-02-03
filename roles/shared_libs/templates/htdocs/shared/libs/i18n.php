<?php
class I18N 
{
    public static function escapeAttribute($value)
    {
        $value = str_replace(
            array( "\"", "<", ">" ),
            array( "&quot;", "&lt;", "&gt;" ),
            $value
        ); 
        return $value;
    }
}
