CREATE OR REPLACE VIEW v_geocoding_month_calls
AS
	SELECT
		COUNT(*)::int AS count
	FROM geocache
	WHERE
    	del_ts IS NULL
        AND ins_ts >= NOW() - INTERVAL '30 days'
;
