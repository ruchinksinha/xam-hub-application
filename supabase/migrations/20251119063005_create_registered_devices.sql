/*
  # Create registered_devices table

  1. New Tables
    - `registered_devices`
      - `id` (uuid, primary key) - Unique identifier for the registration record
      - `serial` (text, unique, not null) - Device serial number from ADB
      - `name` (text) - Friendly name for the device
      - `model` (text) - Device model information
      - `manufacturer` (text) - Device manufacturer
      - `registered_at` (timestamptz, default now()) - When the device was registered
      - `last_seen_at` (timestamptz) - Last time device was connected
      - `is_connected` (boolean, default false) - Current connection status
      - `usb_bus` (text) - USB bus identifier
      - `usb_device` (text) - USB device identifier
      - `notes` (text) - Optional notes about the device

  2. Security
    - Enable RLS on `registered_devices` table
    - Add policy for public access (no auth required for this application)

  3. Indexes
    - Index on serial for fast lookups
    - Index on is_connected for filtering connected devices
*/

CREATE TABLE IF NOT EXISTS registered_devices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  serial text UNIQUE NOT NULL,
  name text DEFAULT '',
  model text DEFAULT '',
  manufacturer text DEFAULT '',
  registered_at timestamptz DEFAULT now(),
  last_seen_at timestamptz,
  is_connected boolean DEFAULT false,
  usb_bus text DEFAULT '',
  usb_device text DEFAULT '',
  notes text DEFAULT ''
);

ALTER TABLE registered_devices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all access to registered_devices"
  ON registered_devices
  FOR ALL
  TO public
  USING (true)
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_registered_devices_serial ON registered_devices(serial);
CREATE INDEX IF NOT EXISTS idx_registered_devices_is_connected ON registered_devices(is_connected);