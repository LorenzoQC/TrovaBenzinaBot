CREATE OR REPLACE VIEW v_users_searches_stats
AS
	SELECT
    	s.user_id AS user_id,
    	s.fuel_id AS fuel_id,
    	f.code AS fuel_code,
    	f.name AS fuel_name,
    	f.uom AS uom,
    	f.avg_consumption_per_100km AS avg_consumption_per_100km,
    	COUNT(*) AS num_searches,
    	SUM(s.num_stations) AS num_stations,
    	AVG(s.price_avg) - AVG(s.price_min) AS avg_eur_save_per_unit,
    	(AVG(s.price_avg) - AVG(s.price_min)) / AVG(s.price_avg) AS avg_pct_save,
    	(AVG(s.price_avg) - AVG(s.price_min)) * (f.avg_consumption_per_100km * 100) AS estimated_annual_save_eur
	FROM searches s
    JOIN dom_fuels f
      	ON s.fuel_id = f.id
	WHERE
	    s.radius = 7
	    AND s.price_avg IS NOT NULL
	    AND s.price_min IS NOT NULL
	    AND s.del_ts IS NULL
	GROUP BY
    	s.user_id,
    	s.fuel_id,
	    f.code,
	    f.name,
	    f.uom,
	    f.avg_consumption_per_100km
;
