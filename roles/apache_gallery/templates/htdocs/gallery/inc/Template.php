<?php
class Template {

    public static function getStarttime($images)
    {
        $starttime = clone $images[0]->getTime();
        $starttime->setTime($starttime->format('H'),0,0,0);
        $starttime->add(new DateInterval('PT1H'));
        return $starttime;
    }
    
    public static function getEndtime($images)
    {
        $endtime = clone $images[count($images)-1]->getTime();
        $endtime->setTime($endtime->format('H'),0,0,0);
        return $endtime;
    }
    
    public static function getSlots($starttime,$endtime,$images)
    {
        $_diff = $starttime->diff($endtime);
        $_hours = $_diff->h;
        $_hours = $_hours + ($_diff->days*24);

        if( $_hours == 0 ) return "<div style=\"margin: auto;\">No images available</div>";

        $_max_steps = 100;
        $stepDurationInHours = ceil($_hours / $_max_steps);

        $grouped_images = array();
        $currenttime = clone $starttime;
        while( $currenttime->getTimestamp() >= $endtime->getTimestamp() )
        {
            $grouped_images[$currenttime->getTimestamp()] = array();
            $currenttime->sub(new DateInterval('PT'.$stepDurationInHours.'H'));
        }
        
        foreach( $images as $image ){
            $current_step_time = clone $image->getTime();
            $current_step_time->setTime($current_step_time->format('H'),0,0,0);
            $current_step_time->add(new DateInterval('PT1H'));
            
            //if( !isset($grouped_images[$current_step_time->getTimestamp()]) )
            //{
            //    echo "missing " . $current_step_time->format("d.m H:i:s") . "\n";
            //}
            
            array_push($grouped_images[$current_step_time->getTimestamp()],$image);
        }    
        
        $max_count = 0;
        foreach( $grouped_images as $key => $value )
        {
            if( $max_count < count($value) ) $max_count = count($value);
        }
        
        $html = "";
        $lastLabledDate = NULL;
        $lastLabledTime = NULL;
        foreach( $grouped_images as $key => $values )
        {
            $time = new DateTime();
            $time->setTimestamp($key);
                
            $html .= "<div class='slot";
            
            if( count($values) > 0 )
            {
                $html .= " filled' onclick='mx.Gallery.jumpToSlot(" . $key . ")";
            }
            
            if( count($values) > 0 )
            {
                $html .= "' data-formattedtime='" . $time->format('d.m. H:i') . "' data-count='" . count($values);
            }
            
            $html .= "' data-timeslot='" . $key . "'>";
            
            if( $lastLabledDate == NULL || $lastLabledDate->format("d") != $time->format("d") )
            {
                $html .= "<div class='date'>" . $time->format('d.m.') . "</div>";
                $lastLabledDate = $time;
            }

            if( $lastLabledTime == NULL || $lastLabledTime->getTimestamp() - $key > (60*60*12) )
            {   
                $time = new DateTime();
                $time->setTimestamp($key);
                
                $html .= "<div class='time'>" . $time->format('H:i') . "</div>";
                $lastLabledTime = $time;
            }

            if( count($values) > 0 )
            {
                $html .= "<div class='bar' style='height:" . ceil( count($values) * 100 / $max_count ) . "%'></div>";
            }
            else
            {
                $html .= "<div class='bar' style='height:0'></div>";
            }
            
            //if( 
            
            $html .= "</div>";
        }
        
        return $html;
    }
    
    public static function getImages($images)
    {
        $html = "";
        foreach( $images as $index => $image )
        {
            // add timeslot key
            // add formatted time
            
            $date = clone $image->getTime();
            $formattedTime = $date->format("d.m. H:i:s");
            
            $date->setTime( $date->format("H"), 0, 0, 0 );
            $date->add(new DateInterval('PT1H'));
            
            $html .= "<div class='container' data-index='" . $index . "' onclick='mx.Gallery.openDetails(" . $index . ")' data-src='" . urlencode($image->getFile()) . "' data-formattedtime='" . $formattedTime . "' data-timeslot='" . $date->getTimestamp() . "'><div class='dummy'></div></div>";
        }
        
        return $html;
    }
}
