<?php
class Environment
{
    public static function getInfluxDBIntervalConfigs()
    {
        return array(
            "pGF_Utilityroom_Gas_Current_Daily_Consumption" => new IntervalConfig( "pGF_Utilityroom_Gas_Meter_Current_Count", "daily", "0 */5 * * * ?", 20 ),
            "pGF_Utilityroom_Gas_Current_Consumption" => new IntervalConfig("pGF_Utilityroom_Gas_Meter_Current_Count", "interval", "0 */5 * * * ?", 0.2, 300, 615, 900, 2 ),

            //"Electricity_Current_Daily_Consumption" => new IntervalConfig("Electricity_Meter", "daily", "15 */5 * * * ?", 50 ),
            //"Electricity_Current_Consumption" => new IntervalConfig("Electricity_Meter", "interval", "15 */5 * * * ?", 20000, 300, 360, 900, 2 ),

            #"Wind_Garden_Current" => new IntervalConfig("Wind_Garden_Converted", "interval", "0 */15 * * * ?", 150, "MAX", 900, 900, 99 ),
            #"Rain_Garden_Current" => new IntervalConfig("Rain_Garden_Counter", "interval", "0 0 * * * ?", 30, "DIFF", 3600, 3600, 99 ),
            #"Rain_Garden_Current_Daily" => new IntervalConfig("Rain_Garden_Counter", "daily", "0 */5 * * * ?", 100 ),

            "pOutdoor_WeatherStation_Wind_Current" => new IntervalConfig("pOutdoor_WeatherStation_Wind_Speed", "interval", "0 */15 * * * ?", 150, "MAX", 900, 900, 99 ),
            "pOutdoor_WeatherStation_Rain_Current" => new IntervalConfig("pOutdoor_WeatherStation_Rain_Counter", "interval", "0 0 * * * ?", 30, "DIFF", 3600, 3600, 99 ),
            "pOutdoor_WeatherStation_Rain_Daily" => new IntervalConfig("pOutdoor_WeatherStation_Rain_Counter", "daily", "0 */5 * * * ?", 100 ),

            // Maybe improve interval. Sometimes we messure every minute
            "pGF_Utilityroom_Heating_Burner_Hours_Current_Daily" => new IntervalConfig("pGF_Utilityroom_Heating_Burner_Hours", "daily", "15 0 0 * * ?", 15 ),
            "pGF_Utilityroom_Heating_Burner_Starts_Current_Daily" => new IntervalConfig("pGF_Utilityroom_Heating_Burner_Starts", "daily", "15 0 0 * * ?", 100 ),

            "pGF_Utilityroom_Heating_Solar_Power_Current_Daily" => new IntervalConfig("pGF_Utilityroom_Heating_Solar_Power", "daily", "15 0 0 * * ?", 50 ),
            "pGF_Utilityroom_Heating_Solar_Power_Current5Min" => new IntervalConfig("pGF_Utilityroom_Heating_Solar_Power", "interval", "45 */30 * * * ?", 30, 300, 3600, 5600, 2 ),
        );
    }
    
    public static function getInfluxPersistanceGroups()
    {
        return array( 'gPersistance_Chart' );
    }

    public static function getMySQLIntervalConfigs()
    {
        return array(
            "Electricity_Current_Daily_Consumption" => new IntervalConfig("Electricity_Meter_Demand", "daily", "15 */5 * * * ?", 50 ),
            "Electricity_Current_Consumption" => new IntervalConfig("Electricity_Meter_Demand", "interval", "15 */5 * * * ?", 20000, 300, 360, 900, 2 ),
            "Electricity_Current_Daily_Demand" => new IntervalConfig("Electricity_Meter_Demand", "daily", "15 */5 * * * ?", 50 )
        );
    }
    
    public static function getMySQLPersistanceGroups()
    {
        return array(
            "gPersistance_History",
            "gGF_Sensor_Window",
            "gFF_Sensor_Window"
        );     
    }
}
 
