CREATE OR REPLACE FUNCTION letter_to_number(input_text TEXT) RETURNS INTEGER AS $$
DECLARE
  result INTEGER := 0;
  i INTEGER;
BEGIN
  FOR i IN 1..LENGTH(input_text) LOOP
    result := result * 26 + (ASCII(SUBSTRING(input_text FROM i FOR 1)) - ASCII('A') + 1);
  END LOOP;
  RETURN result;
END;
$$ LANGUAGE plpgsql;