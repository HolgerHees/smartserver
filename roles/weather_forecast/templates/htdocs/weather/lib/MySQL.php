<?php

class MySQL
{
    /* @var $connection mysqli */
    private $connection;

    /**
     * MySQL constructor.
     * @param $config
     */
    public function __construct( $host, $user, $pass, $dbname )
    {
        $this->connection = new mysqli( $host, $user, $pass );
        if( $this->connection->connect_error )
        {
            error_log( 'Can\'t connect: ' . $this->connection->connect_error );
            return false;
        }

        $db_selected = $this->connection->select_db( $dbname );
        if( !$db_selected )
        {
            error_log( 'Can\'t use ' . $dbname . ' : ' . $this->connection->connect_error );
            return false;
        }
    }

    public function getWeatherData( $offset )
    {
        $result = $this->query( "SELECT * FROM ".DB_TABLE." WHERE `datetime` > DATE_ADD(NOW(), INTERVAL " . ( $offset - 1 ) . " HOUR)  ORDER BY `datetime` ASC LIMIT 1" );

        if( $result->num_rows > 0 )
        {
            while( $data = $result->fetch_assoc() )
            {
                $this->prepateDatetime($data);
                return $data;
            }
        }
        return null;
    }
    
    public function getWeatherDataList($from, $to)
    {
		//echo "SELECT * FROM ".DB_TABLE." WHERE `datetime` >= '".$from->format("Y-m-d H:i:s")."' AND `datetime` <= '".$to->format("Y-m-d H:i:s")."'  ORDER BY `datetime`";
    
        $result = $this->query( "SELECT * FROM ".DB_TABLE." WHERE `datetime` >= '".$from->format("Y-m-d H:i:s")."' AND `datetime` < '".$to->format("Y-m-d H:i:s")."'  ORDER BY `datetime`" );

        if( $result->num_rows > 0 )
        {
			$list = array();
            while( $data = $result->fetch_assoc() )
            {
                $this->prepateDatetime($data);
                $list[] = $data;
            }
            return $list;
        }
        return null;
    }
    
    public function getWeatherDataWeekList($from)
    {
        $result = $this->query( "SELECT * FROM ".DB_TABLE." WHERE `datetime` >= '".$from->format("Y-m-d H:i:s")."' AND `datetime` < DATE_ADD(CURDATE(), INTERVAL 8 DAY)  ORDER BY `datetime`" );

        if( $result->num_rows > 0 )
        {
			$list = array();
            while( $data = $result->fetch_assoc() )
            {
                $this->prepateDatetime($data);
                $list[] = $data;
            }
            return $list;
        }
        return null;
    }

    private function prepateDatetime(&$data)
    {
        global $GLOBAL_TIMEZONE;
        
        $data['datetime'] = DateTime::createFromFormat('Y-m-d H:i:s',$data['datetime']);
        $data['datetime']->setTimezone($GLOBAL_TIMEZONE);
    }
    
    private function query( $sql )
    {
        $result = @$this->connection->query( $sql );

        if( $result === false )
        {
            error_log( 'Invalid query: ' . $this->connection->errno . " " . $this->connection->error . " for query '" . $sql . "'" );
        }

        return $result;
    }
}
