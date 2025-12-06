import React from 'react';
import { BarChart3, Users, Clock, TrendingUp, Target, MessageSquare } from 'lucide-react';
import { Card } from '@/components/ui/card';

export const InsightsDashboard: React.FC = () => {
  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="p-4 border-b border-white/10">
        <h2 className="text-lg font-semibold flex items-center space-x-2">
          <BarChart3 className="w-5 h-5" />
          <span>Meeting Insights</span>
        </h2>
      </div>

      <div className="flex-1 p-4 space-y-4 overflow-y-auto">
        {/* Speaking Time */}
        <Card className="p-4 bg-white/5 border-white/10">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Users className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium">Speaking Time</span>
            </div>
            <span className="text-xs text-gray-400">Total: 45min</span>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs">John</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500" style={{ width: '40%' }} />
                </div>
                <span className="text-xs">40%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs">Sarah</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500" style={{ width: '35%' }} />
                </div>
                <span className="text-xs">35%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs">Mike</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500" style={{ width: '25%' }} />
                </div>
                <span className="text-xs">25%</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Topics */}
        <Card className="p-4 bg-white/5 border-white/10">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-green-400" />
              <span className="text-sm font-medium">Key Topics</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-full">Product Roadmap</span>
            <span className="px-2 py-1 bg-green-500/20 text-green-300 text-xs rounded-full">Q4 Planning</span>
            <span className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded-full">Budget Review</span>
            <span className="px-2 py-1 bg-orange-500/20 text-orange-300 text-xs rounded-full">Team Updates</span>
          </div>
        </Card>

        {/* Sentiment */}
        <Card className="p-4 bg-white/5 border-white/10">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-medium">Sentiment Analysis</span>
            </div>
            <span className="text-xs text-green-400">Positive</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden flex">
              <div className="bg-green-500" style={{ width: '65%' }} />
              <div className="bg-yellow-500" style={{ width: '25%' }} />
              <div className="bg-red-500" style={{ width: '10%' }} />
            </div>
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-400">
            <span>65% Positive</span>
            <span>25% Neutral</span>
            <span>10% Negative</span>
          </div>
        </Card>

        {/* Action Items */}
        <Card className="p-4 bg-white/5 border-white/10">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-4 h-4 text-red-400" />
              <span className="text-sm font-medium">Action Items</span>
            </div>
            <span className="text-xs bg-red-500/20 text-red-300 px-2 py-1 rounded">3</span>
          </div>
          <div className="space-y-2">
            <div className="text-xs p-2 bg-white/5 rounded">
              <div className="font-medium text-blue-300">Research competitor analysis</div>
              <div className="text-gray-400">Assigned to: John • Due: Next week</div>
            </div>
            <div className="text-xs p-2 bg-white/5 rounded">
              <div className="font-medium text-green-300">Prepare Q4 budget proposal</div>
              <div className="text-gray-400">Assigned to: Sarah • Due: Friday</div>
            </div>
            <div className="text-xs p-2 bg-white/5 rounded">
              <div className="font-medium text-purple-300">Schedule team building event</div>
              <div className="text-gray-400">Assigned to: Mike • Due: Next month</div>
            </div>
          </div>
        </Card>

        {/* Meeting Duration */}
        <Card className="p-4 bg-white/5 border-white/10">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-medium">Meeting Duration</span>
            </div>
            <span className="text-xs text-gray-400">00:45:23</span>
          </div>
          <div className="text-xs text-gray-400">
            <div>Scheduled: 1 hour</div>
            <div>Efficiency: 75% (on track)</div>
          </div>
        </Card>
      </div>
    </div>
  );
};
