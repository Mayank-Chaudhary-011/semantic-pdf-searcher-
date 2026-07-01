// supabaseClient.js
// Initializes and exports a single Supabase client instance.
// All auth, db, and storage calls in the app go through this one object.

import { createClient } from "@supabase/supabase-js";

// These come from frontend/.env — never hardcode keys here
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// createClient sets up the connection to your Supabase project
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
