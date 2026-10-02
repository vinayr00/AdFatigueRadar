import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { X, Loader2, Sparkles } from "lucide-react";
import { useUIStore } from "../../store/uiStore";
import { useCreateCampaign } from "../../hooks/useCampaigns";
import { Platform } from "../../types/contracts";
import { apiFetch } from "../../api/client";

const campaignSchema = z.object({
  name: z.string().min(3, "Campaign name must be at least 3 characters"),
  platform: z.enum(["meta", "google", "tiktok", "youtube", "x"]),
  category: z.string().min(2, "Category is required"),
  target_audience: z.string().min(2, "Target audience is required"),
  budget: z.coerce.number().min(10, "Minimum budget is ₹100/day"),
  date_range: z.string().min(5, "Date range is required"),
});

type CampaignFormValues = z.infer<typeof campaignSchema>;

export const CreateCampaignDialog: React.FC = () => {
  const { createCampaignModalOpen, setCreateCampaignModalOpen } = useUIStore();
  const createCampaignMutation = useCreateCampaign();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CampaignFormValues>({
    resolver: zodResolver(campaignSchema),
    defaultValues: {
      name: "",
      platform: "meta",
      category: "Fashion & Apparel",
      target_audience: "Broad Audience 18-45",
      budget: 100,
      date_range: "Jul 01, 2024 – Jul 31, 2024",
    },
  });

  if (!createCampaignModalOpen) return null;

  const onSubmit = async (data: CampaignFormValues) => {
    try {
      const created = await createCampaignMutation.mutateAsync({
        name: data.name,
        platform: data.platform as Platform,
        category: data.category,
        target_audience: data.target_audience,
        date_range: data.date_range,
      });

      // ONLY AFTER successful campaign creation, initialize demo JSON
      if (created && created.id) {
        localStorage.setItem("active_demo_campaign", created.id);
        await apiFetch(`/api/demo/campaigns/${encodeURIComponent(created.id)}/init`, {
          method: "POST",
          body: JSON.stringify({ name: created.name }),
        }).catch(() => {});
      }

      reset();
      setCreateCampaignModalOpen(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 relative animate-in zoom-in-95 duration-200">
        <button
          onClick={() => setCreateCampaignModalOpen(false)}
          className="absolute top-5 right-5 p-2 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 mb-1">
          <div className="w-8 h-8 rounded-xl bg-[#E4EFE3] text-[#2D5A3C] flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <h3 className="text-xl font-bold font-serif text-slate-900">Create New Campaign</h3>
        </div>
        <p className="text-xs text-slate-500 mb-6">
          Configure telemetry observation and audience fatigue guard parameters.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Campaign Name</label>
            <input
              {...register("name")}
              placeholder="e.g. Autumn Warmth Promo 2024"
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
            />
            {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Platform</label>
              <select
                {...register("platform")}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
              >
                <option value="meta">Meta Ads</option>
                <option value="google">Google Ads</option>
                <option value="tiktok">TikTok Ads</option>
                <option value="youtube">YouTube Ads</option>
                <option value="x">X (Twitter) Ads</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Daily Budget (₹)</label>
              <input
                type="number"
                {...register("budget")}
                className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
              />
              {errors.budget && <p className="text-xs text-red-500 mt-1">{errors.budget.message}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
              <input
                {...register("category")}
                placeholder="e.g. Fashion & Apparel"
                className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Date Range</label>
              <input
                {...register("date_range")}
                placeholder="Jul 01, 2024 – Jul 31, 2024"
                className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Audience</label>
            <input
              {...register("target_audience")}
              placeholder="e.g. Lookalike 1% + In-Market Buyers"
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
            />
          </div>

          <div className="pt-3 flex items-center justify-end gap-2.5 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setCreateCampaignModalOpen(false)}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || createCampaignMutation.isPending}
              className="px-5 py-2 text-xs font-semibold text-white bg-[#E85D35] hover:bg-[#D54D26] rounded-xl transition-colors flex items-center gap-2 shadow-sm disabled:opacity-60"
            >
              {(isSubmitting || createCampaignMutation.isPending) && (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              )}
              Create Campaign
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
