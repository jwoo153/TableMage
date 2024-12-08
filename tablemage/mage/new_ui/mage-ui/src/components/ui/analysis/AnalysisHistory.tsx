'use client'

import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { AnalysisItem } from '@/lib/api'

interface AnalysisHistoryProps {
  items: AnalysisItem[]
}

export default function AnalysisHistory({ items }: AnalysisHistoryProps) {
  return (
    <div className="border bg-gray-50 rounded-lg overflow-hidden flex flex-col" style={{ height: '70vh' }}>
      <div className="bg-white p-4 border-b">
        <h2 className="text-lg font-semibold">Analysis Results</h2>
      </div>
      
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4 pr-4 max-w-4xl mx-auto">
          {items.length === 0 ? (
            <div className="text-gray-500 text-center p-4">
              No analysis results yet. Try asking a question about your data!
            </div>
          ) : (
            items.map((item, index) => (
              <Card key={index} className="p-4 bg-white shadow-sm w-full">
                {item.file_type === 'figure' && (
                  <div className="w-full overflow-x-auto">
                    <div className="inline-block min-w-min">
                      <img
                        src={`http://localhost:5005/api/analysis/file/${item.file_name}`}
                        alt="Analysis Figure"
                        className="h-auto rounded-lg"
                      />
                    </div>
                  </div>
                )}
                
                {item.file_type === 'table' && (
                  <div 
                    className="w-full overflow-x-auto"
                    style={{ maxWidth: 'calc(100% - 2rem)' }}
                    dangerouslySetInnerHTML={{ __html: item.content || '' }}
                  />
                )}
                
                {item.file_type === 'thought' && (
                  <div 
                    className="prose w-full overflow-x-auto"
                    style={{ maxWidth: 'calc(100% - 2rem)' }}
                  >
                    {item.content}
                  </div>
                )}
                
                {item.file_type === 'code' && (
                  <div className="w-full overflow-x-auto" style={{ maxWidth: 'calc(100% - 2rem)' }}>
                    <pre className="bg-gray-100 p-4 rounded-lg text-sm whitespace-pre inline-block min-w-min">
                      <code>{item.content}</code>
                    </pre>
                  </div>
                )}
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}