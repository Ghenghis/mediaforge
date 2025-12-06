export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.5"
  }
  public: {
    Tables: {
      actor_portrait_history: {
        Row: {
          actor_id: string
          color_mode: string
          created_at: string
          generation_params: Json | null
          id: string
          image_url: string
          is_current: boolean
        }
        Insert: {
          actor_id: string
          color_mode?: string
          created_at?: string
          generation_params?: Json | null
          id?: string
          image_url: string
          is_current?: boolean
        }
        Update: {
          actor_id?: string
          color_mode?: string
          created_at?: string
          generation_params?: Json | null
          id?: string
          image_url?: string
          is_current?: boolean
        }
        Relationships: [
          {
            foreignKeyName: "actor_portrait_history_actor_id_fkey"
            columns: ["actor_id"]
            isOneToOne: false
            referencedRelation: "actors"
            referencedColumns: ["id"]
          },
        ]
      }
      actors: {
        Row: {
          bio: string
          character_type: string | null
          created_at: string
          era: string
          first_name: string
          full_name: string | null
          id: string
          image_url: string | null
          last_name: string
          metadata: Json | null
          middle_name: string | null
          role: string
          tags: string[] | null
          updated_at: string
          voice_id: string | null
          voice_provider: string | null
          voice_settings: Json | null
        }
        Insert: {
          bio: string
          character_type?: string | null
          created_at?: string
          era?: string
          first_name: string
          full_name?: string | null
          id?: string
          image_url?: string | null
          last_name: string
          metadata?: Json | null
          middle_name?: string | null
          role: string
          tags?: string[] | null
          updated_at?: string
          voice_id?: string | null
          voice_provider?: string | null
          voice_settings?: Json | null
        }
        Update: {
          bio?: string
          character_type?: string | null
          created_at?: string
          era?: string
          first_name?: string
          full_name?: string | null
          id?: string
          image_url?: string | null
          last_name?: string
          metadata?: Json | null
          middle_name?: string | null
          role?: string
          tags?: string[] | null
          updated_at?: string
          voice_id?: string | null
          voice_provider?: string | null
          voice_settings?: Json | null
        }
        Relationships: []
      }
      portrait_collection_presets: {
        Row: {
          collection_id: string
          created_at: string
          display_order: number | null
          id: string
          preset_id: string
        }
        Insert: {
          collection_id: string
          created_at?: string
          display_order?: number | null
          id?: string
          preset_id: string
        }
        Update: {
          collection_id?: string
          created_at?: string
          display_order?: number | null
          id?: string
          preset_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "portrait_collection_presets_collection_id_fkey"
            columns: ["collection_id"]
            isOneToOne: false
            referencedRelation: "portrait_preset_collections"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "portrait_collection_presets_preset_id_fkey"
            columns: ["preset_id"]
            isOneToOne: false
            referencedRelation: "portrait_presets"
            referencedColumns: ["id"]
          },
        ]
      }
      portrait_preset_collections: {
        Row: {
          created_at: string
          creator_name: string | null
          description: string | null
          id: string
          is_public: boolean | null
          is_randomized: boolean | null
          name: string
          randomization_rules: Json | null
          tags: string[] | null
          thumbnail_url: string | null
          updated_at: string
        }
        Insert: {
          created_at?: string
          creator_name?: string | null
          description?: string | null
          id?: string
          is_public?: boolean | null
          is_randomized?: boolean | null
          name: string
          randomization_rules?: Json | null
          tags?: string[] | null
          thumbnail_url?: string | null
          updated_at?: string
        }
        Update: {
          created_at?: string
          creator_name?: string | null
          description?: string | null
          id?: string
          is_public?: boolean | null
          is_randomized?: boolean | null
          name?: string
          randomization_rules?: Json | null
          tags?: string[] | null
          thumbnail_url?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      portrait_preset_reviews: {
        Row: {
          created_at: string
          id: string
          is_verified: boolean
          preset_id: string
          rating: number
          review_text: string | null
          reviewer_name: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string
          id?: string
          is_verified?: boolean
          preset_id: string
          rating: number
          review_text?: string | null
          reviewer_name?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string
          id?: string
          is_verified?: boolean
          preset_id?: string
          rating?: number
          review_text?: string | null
          reviewer_name?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "portrait_preset_reviews_preset_id_fkey"
            columns: ["preset_id"]
            isOneToOne: false
            referencedRelation: "portrait_presets"
            referencedColumns: ["id"]
          },
        ]
      }
      portrait_preset_versions: {
        Row: {
          accent_focus: string | null
          age: number | null
          change_notes: string | null
          character_details: Json | null
          character_style: string | null
          clothing_formality: number | null
          clothing_style: string | null
          clothing_type: string | null
          contrast: number | null
          coverage: number | null
          created_at: string
          description: string | null
          detail_level: number | null
          fit: string | null
          id: string
          max_age: number | null
          min_age: number | null
          name: string
          preset_id: string
          rating: string | null
          style_profile: string | null
          tags: string[] | null
          texture_detail: number | null
          version_number: number
          weathering: number | null
        }
        Insert: {
          accent_focus?: string | null
          age?: number | null
          change_notes?: string | null
          character_details?: Json | null
          character_style?: string | null
          clothing_formality?: number | null
          clothing_style?: string | null
          clothing_type?: string | null
          contrast?: number | null
          coverage?: number | null
          created_at?: string
          description?: string | null
          detail_level?: number | null
          fit?: string | null
          id?: string
          max_age?: number | null
          min_age?: number | null
          name: string
          preset_id: string
          rating?: string | null
          style_profile?: string | null
          tags?: string[] | null
          texture_detail?: number | null
          version_number: number
          weathering?: number | null
        }
        Update: {
          accent_focus?: string | null
          age?: number | null
          change_notes?: string | null
          character_details?: Json | null
          character_style?: string | null
          clothing_formality?: number | null
          clothing_style?: string | null
          clothing_type?: string | null
          contrast?: number | null
          coverage?: number | null
          created_at?: string
          description?: string | null
          detail_level?: number | null
          fit?: string | null
          id?: string
          max_age?: number | null
          min_age?: number | null
          name?: string
          preset_id?: string
          rating?: string | null
          style_profile?: string | null
          tags?: string[] | null
          texture_detail?: number | null
          version_number?: number
          weathering?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "portrait_preset_versions_preset_id_fkey"
            columns: ["preset_id"]
            isOneToOne: false
            referencedRelation: "portrait_presets"
            referencedColumns: ["id"]
          },
        ]
      }
      portrait_presets: {
        Row: {
          accent_focus: string | null
          age: number | null
          average_rating: number | null
          character_details: Json | null
          character_style: string | null
          clothing_formality: number | null
          clothing_style: string | null
          clothing_type: string | null
          contrast: number | null
          coverage: number | null
          created_at: string
          creator_name: string | null
          current_version: number | null
          description: string | null
          detail_level: number | null
          download_count: number
          fit: string | null
          id: string
          is_public: boolean
          max_age: number | null
          min_age: number | null
          name: string
          rating: string | null
          review_count: number | null
          style_profile: string | null
          tags: string[] | null
          texture_detail: number | null
          thumbnail_url: string | null
          updated_at: string
          weathering: number | null
        }
        Insert: {
          accent_focus?: string | null
          age?: number | null
          average_rating?: number | null
          character_details?: Json | null
          character_style?: string | null
          clothing_formality?: number | null
          clothing_style?: string | null
          clothing_type?: string | null
          contrast?: number | null
          coverage?: number | null
          created_at?: string
          creator_name?: string | null
          current_version?: number | null
          description?: string | null
          detail_level?: number | null
          download_count?: number
          fit?: string | null
          id?: string
          is_public?: boolean
          max_age?: number | null
          min_age?: number | null
          name: string
          rating?: string | null
          review_count?: number | null
          style_profile?: string | null
          tags?: string[] | null
          texture_detail?: number | null
          thumbnail_url?: string | null
          updated_at?: string
          weathering?: number | null
        }
        Update: {
          accent_focus?: string | null
          age?: number | null
          average_rating?: number | null
          character_details?: Json | null
          character_style?: string | null
          clothing_formality?: number | null
          clothing_style?: string | null
          clothing_type?: string | null
          contrast?: number | null
          coverage?: number | null
          created_at?: string
          creator_name?: string | null
          current_version?: number | null
          description?: string | null
          detail_level?: number | null
          download_count?: number
          fit?: string | null
          id?: string
          is_public?: boolean
          max_age?: number | null
          min_age?: number | null
          name?: string
          rating?: string | null
          review_count?: number | null
          style_profile?: string | null
          tags?: string[] | null
          texture_detail?: number | null
          thumbnail_url?: string | null
          updated_at?: string
          weathering?: number | null
        }
        Relationships: []
      }
      stories: {
        Row: {
          audio_url: string | null
          chapter_number: number | null
          created_at: string
          description: string | null
          duration_minutes: number | null
          era: string
          id: string
          master_volume: number | null
          metadata: Json | null
          pause_duration: number | null
          published_at: string | null
          script_content: string | null
          status: string | null
          title: string
          updated_at: string
          video_url: string | null
        }
        Insert: {
          audio_url?: string | null
          chapter_number?: number | null
          created_at?: string
          description?: string | null
          duration_minutes?: number | null
          era: string
          id?: string
          master_volume?: number | null
          metadata?: Json | null
          pause_duration?: number | null
          published_at?: string | null
          script_content?: string | null
          status?: string | null
          title: string
          updated_at?: string
          video_url?: string | null
        }
        Update: {
          audio_url?: string | null
          chapter_number?: number | null
          created_at?: string
          description?: string | null
          duration_minutes?: number | null
          era?: string
          id?: string
          master_volume?: number | null
          metadata?: Json | null
          pause_duration?: number | null
          published_at?: string | null
          script_content?: string | null
          status?: string | null
          title?: string
          updated_at?: string
          video_url?: string | null
        }
        Relationships: []
      }
      story_actors: {
        Row: {
          actor_id: string
          character_name: string | null
          created_at: string
          id: string
          speaking_order: number | null
          story_id: string
        }
        Insert: {
          actor_id: string
          character_name?: string | null
          created_at?: string
          id?: string
          speaking_order?: number | null
          story_id: string
        }
        Update: {
          actor_id?: string
          character_name?: string | null
          created_at?: string
          id?: string
          speaking_order?: number | null
          story_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "story_actors_actor_id_fkey"
            columns: ["actor_id"]
            isOneToOne: false
            referencedRelation: "actors"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "story_actors_story_id_fkey"
            columns: ["story_id"]
            isOneToOne: false
            referencedRelation: "stories"
            referencedColumns: ["id"]
          },
        ]
      }
      story_lines: {
        Row: {
          actor_id: string
          audio_url: string | null
          created_at: string
          fade_in: boolean
          fade_out: boolean
          id: string
          line_number: number
          story_id: string
          text: string
          updated_at: string
          volume: number
        }
        Insert: {
          actor_id: string
          audio_url?: string | null
          created_at?: string
          fade_in?: boolean
          fade_out?: boolean
          id?: string
          line_number: number
          story_id: string
          text: string
          updated_at?: string
          volume?: number
        }
        Update: {
          actor_id?: string
          audio_url?: string | null
          created_at?: string
          fade_in?: boolean
          fade_out?: boolean
          id?: string
          line_number?: number
          story_id?: string
          text?: string
          updated_at?: string
          volume?: number
        }
        Relationships: [
          {
            foreignKeyName: "story_lines_actor_id_fkey"
            columns: ["actor_id"]
            isOneToOne: false
            referencedRelation: "actors"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "story_lines_story_id_fkey"
            columns: ["story_id"]
            isOneToOne: false
            referencedRelation: "stories"
            referencedColumns: ["id"]
          },
        ]
      }
      story_template_lines: {
        Row: {
          actor_first_name: string
          actor_last_name: string
          actor_role: string
          created_at: string
          id: string
          line_number: number
          template_id: string
          text: string
        }
        Insert: {
          actor_first_name: string
          actor_last_name: string
          actor_role: string
          created_at?: string
          id?: string
          line_number: number
          template_id: string
          text: string
        }
        Update: {
          actor_first_name?: string
          actor_last_name?: string
          actor_role?: string
          created_at?: string
          id?: string
          line_number?: number
          template_id?: string
          text?: string
        }
        Relationships: [
          {
            foreignKeyName: "story_template_lines_template_id_fkey"
            columns: ["template_id"]
            isOneToOne: false
            referencedRelation: "story_templates"
            referencedColumns: ["id"]
          },
        ]
      }
      story_templates: {
        Row: {
          created_at: string
          description: string | null
          era: string
          genre: string
          icon_name: string | null
          id: string
          is_active: boolean
          title: string
          updated_at: string
          use_count: number
        }
        Insert: {
          created_at?: string
          description?: string | null
          era?: string
          genre: string
          icon_name?: string | null
          id?: string
          is_active?: boolean
          title: string
          updated_at?: string
          use_count?: number
        }
        Update: {
          created_at?: string
          description?: string | null
          era?: string
          genre?: string
          icon_name?: string | null
          id?: string
          is_active?: boolean
          title?: string
          updated_at?: string
          use_count?: number
        }
        Relationships: []
      }
      storyboard_scenes: {
        Row: {
          created_at: string
          era: string
          id: string
          image_url: string | null
          line_range_end: number
          line_range_start: number
          mood: string | null
          scene_description: string
          scene_number: number
          setting: string | null
          story_id: string
          time_of_day: string | null
          updated_at: string
          weather: string | null
        }
        Insert: {
          created_at?: string
          era: string
          id?: string
          image_url?: string | null
          line_range_end: number
          line_range_start: number
          mood?: string | null
          scene_description: string
          scene_number: number
          setting?: string | null
          story_id: string
          time_of_day?: string | null
          updated_at?: string
          weather?: string | null
        }
        Update: {
          created_at?: string
          era?: string
          id?: string
          image_url?: string | null
          line_range_end?: number
          line_range_start?: number
          mood?: string | null
          scene_description?: string
          scene_number?: number
          setting?: string | null
          story_id?: string
          time_of_day?: string | null
          updated_at?: string
          weather?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "storyboard_scenes_story_id_fkey"
            columns: ["story_id"]
            isOneToOne: false
            referencedRelation: "stories"
            referencedColumns: ["id"]
          },
        ]
      }
      user_favorite_presets: {
        Row: {
          created_at: string | null
          id: string
          preset_id: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          id?: string
          preset_id?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          id?: string
          preset_id?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "user_favorite_presets_preset_id_fkey"
            columns: ["preset_id"]
            isOneToOne: false
            referencedRelation: "portrait_presets"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
