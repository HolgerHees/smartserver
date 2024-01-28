<?php 
class Auth
{
    public static function getUser()
    {
        return $_SERVER['REMOTE_USERNAME'];
    }

    public static function getFullname() 
    {
        return trim($_SERVER['REMOTE_USERFULLNAME']);
    }

    public static function getFirstname()
    {
        return explode(",",trim($_SERVER['REMOTE_USERFULLNAME']))[0];
    }

    public static function getGroups()
    {
        return explode(",",trim($_SERVER['REMOTE_USERGROUP']));
    }

    public static function hasGroup($group) 
    {
        return in_array($group,Auth::getGroups());
    }
}
