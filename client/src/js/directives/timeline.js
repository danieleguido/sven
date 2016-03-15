'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # timeline directive. Create a comparative timeline visualisation from two series of date object:
 * [{day: 'YYY-MM-DD', count: 2}, {day: 'YYY-MM-DD', count: 1}...]
 * 
 */
 angular.module('sven')
  .directive('timeline', function ($log, $window) {
    return {
      restrict: 'EA',
      scope: {
        values: '=',
        filters : '=',
        onbrush: '&',
        onclean: '&'
      },
      template: '<div class="brushdate left "></div><div class="brushdate right "></div><div class="date left "></div><div class="date right "></div><div class="mouse tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div><div class="viewer"></div>',
      link : function(scope, element, attrs) {
        
        var tim = {
              css:{},
              fn:{
                asDay: d3.time.format("%B %d, %Y"),
                asMonth: d3.time.format("%Y-%m"),
                asYear: d3.time.format("%Y")
              }
            };
        
        tim.padding = {
          v: 10,
          h: 10  
        };
        
        tim.dimensions = {
          w: 1000,
          h: 50  
        };
        
        tim.fn.x = d3.time.scale()
            .range([tim.padding.h * 2, tim.dimensions.w - tim.padding.h * 2]);
        tim.fn.x.domain([0, 100]);
        tim.fn.y = d3.scale.sqrt()
            .range([30, 0]);
        


        tim.init = function() {
          tim.viewer      = d3.select('#timeline .viewer');
          tim.tooltip     = d3.select('#timeline .tooltip');
          tim.tooltipText = d3.select('#timeline .tooltip-inner');
          tim.dateLeft    = d3.select('#timeline .date.left');
          tim.dateRight   = d3.select('#timeline .date.right');
          tim.brushDateLeft    = d3.select('#timeline .brushdate.left');
          tim.brushDateRight   = d3.select('#timeline .brushdate.right');
              
          tim.brush       = d3.svg.brush().x(tim.fn.x);
          
          tim.svg     = tim.viewer
            .append("svg")
              .attr("height", tim.dimensions.h)
              .attr("width", tim.dimensions.w);
          
          tim.stream  = tim.svg.append("path")
            .attr("transform", "translate("+ tim.padding.v +"," + tim.padding.h + ")")
            .attr("class", "stream")
          
          tim.pointer = tim.svg.append("rect")
            .attr({
              height: tim.dimensions.h,
              width: 1,
              fill: 'magenta'
            })
            .style({
              'opacity': 0
            })
            
          tim.context = tim.svg.append("g")
              .attr("class", "context")
              .attr("transform", "translate(" + tim.padding.v + "," + tim.padding.h/2 + ")"),                
          
          tim.gBrush = tim.context.append("g")
              .attr("class", "x brush")
              .call(tim.brush);

           tim.gBrush.selectAll("rect")
                  .attr({
                    y: 0,
                    height: tim.dimensions.h - tim.padding.h
                  });

          
          tim.area = d3.svg.area()
              //.interpolate("monotone")
              .x(function (d) {
                return tim.fn.x(d.t);
              })
              .y0(function (d) {
                return tim.fn.y(d.weight);
              })
              .y1(30);
          
          tim.evaluate = function() {
            if(!tim.timeExtent)
              return false
            if(!scope.filters.date__gte && !scope.filters.date__lte) {
              tim.clear();
              return false
              
            }
            // evaluate scope .filters agains the current timeExtension and decide if thiere is the need for updating
            var left = scope.filters.date__gte? d3.time.format("%Y-%m-%d").parse(scope.filters.date__gte): tim.timeExtent[0],
                right = scope.filters.date__lte? d3.time.format("%Y-%m-%d").parse(scope.filters.date__lte): tim.timeExtent[1],
                proceed = left != tim.left || right != tim.right;
                
            tim.left = left;
            tim.right = right;
            $log.log('::timeline evaluate -tochange:', proceed)
            return proceed;
          }

          tim.clear = function() {
            tim.gBrush.call(tim.brush.clear());
            tim.drawDates()
          }

          tim.drawDates = function (extent) {
            if(!extent) {
              tim.brushDateLeft.style({
                visibility: 'hidden'
              });
              tim.brushDateRight.style({
                visibility: 'hidden'
              });
              return;
            }
            if(typeof extent[0] == 'object') {
                tim.brushDateLeft.style({
                visibility: 'visible',
                // transform: 'translateX(' + (tim.fn.x(extent[0]) + 50) +'px)'
              }).text(tim.fn.asDay(extent[0]));
            } else if(typeof extent[0] == 'number') {
                tim.brushDateLeft.style({
                visibility: 'visible',
                // transform: 'translateX(' + (tim.fn.x(extent[0]) + 50) +'px)'
              }).text(tim.fn.asDay(new Date(extent[0])));
            } else {
              tim.brushDateLeft.style({
                visibility: 'hidden'
              });
            }
          
            if(typeof extent[1] == 'object') {
              tim.brushDateRight.style({
                visibility: 'visible',
               // transform: 'translateX(' + (tim.fn.x(extent[1]) + 110 + 50) +'px)'
              }).text(tim.fn.asDay(extent[1]));
            } else if(typeof extent[1] == 'number') {
              tim.brushDateRight.style({
                visibility: 'visible',
               // transform: 'translateX(' + (tim.fn.x(extent[1]) + 110 + 50) +'px)'
              }).text(tim.fn.asDay(new Date(extent[1])));
            } else {
              tim.brushDateRight.style({
                visibility: 'hidden'
              });
            }
          }
        
          tim.brush.on("brush", function() {
            var extent  = tim.brush.extent();
            tim.drawDates(extent);
          });

          tim.brush.on("brushend", function() {
            var extent  = tim.brush.extent(),
                left    = +extent[0],
                right   = +extent[1];
            $log.log('::timeline @brushend, ', left, right);
            if(left == right) {
              $log.log('::timeline @brushend, click on the timeline just clear the things');
              tim.clear();
              scope.onclean({
                keys: ['date__gte','date__lte'], 
                filters: [ 
                  d3.time.format("%Y-%m-%d")(new Date(extent[0])),
                  d3.time.format("%Y-%m-%d")(new Date(extent[1]))
                ]
              })
              scope.$apply();
              return;
            }
            // extent cover the whole timespan
            if(left == tim.timeExtent[0] && right == tim.timeExtent[1]) {
              $log.log('::timeline @brushend, maximum timespan, clear filters');
              tim.clear();
              return;
            }
            $log.log('::timeline @brushend, visualize dates');

            if(!extent[0] || !extent[1])
              return;
            
            tim.drawDates(extent);

            clearTimeout(tim.brushTimer);
            tim.brushTimer = setTimeout(function(){
              // console.log('::timeline @brush, timer end', extent)
              // console.log(d3.time.format("%Y-%m-%d")(extent[0]))
              //console.log(d3.time.format("%Y-%m-%d")(extent[0]))
              
              scope.onbrush({
                keys:[
                  'start',
                  'end',
                ],
                filters: [
                  d3.time.format("%Y-%m-%d")(new Date(extent[0])),
                  d3.time.format("%Y-%m-%d")(new Date(extent[1]))
                ]
              });
              scope.$apply();
            }, 450)
            
            //console.log("brushing babe", tim.brush.extent())
          });
          
          tim.svg.on("mouseover", function(){
            tim.tooltip.style({'opacity': 1});
            tim.pointer.style({'opacity': 1})
          });
          
          tim.svg.on("mouseout", function(){
            tim.tooltip.style({'opacity': 0});
            tim.pointer.style({'opacity': 0})
          });
          

          tim.timeFormat = d3.time.format("%B %d, %Y");
          
          tim.svg.on("mousemove", function(){
            var pos = d3.mouse(this),
                date = new Date(tim.fn.x.invert(pos[0]-tim.padding.v));
            
            tim.pointer.style({
              'opacity': pos[0] < tim.padding.v || pos[0] > tim.availableWidth - tim.padding.v? 0:1
            }).attr('x', pos[0])
            tim.tooltip.style({
              'left': pos[0] + 150 + 'px',
              'opacity': pos[0] < tim.padding.v || pos[0] > tim.availableWidth - tim.padding.v? 0:1
            })
            tim.tooltipText.text(
              tim.timeFormat(date)
            );
            
              
          })
          
           tim.availableWidth = tim.viewer[0][0].clientWidth;
          $log.log('::timeline -> init() ');
        };
        
        
        tim.extent = function(extension) {
          
          if(!extension[0] || !extension[1])
            return;
          tim.gBrush.call(tim.brush.extent(extension));
          tim.gBrush.call(tim.brush.event);
        }
        
        tim.draw = function() {
          clearTimeout(tim.resizeTimer);
          if(!tim.viewer)
            return;

          tim.availableWidth = tim.viewer[0][0].clientWidth;
          var parseDate = d3.time.format("%Y-%m-%d").parse;
          var dataset = angular.copy(scope.values).map(function (d) {
                d.t = parseDate(d.day).getTime();
                d.weight = d.count;
                return d;
              }).sort(function (a, b) {
                return a.t < b.t ? -1 : 1
              }),
              ratio = dataset.length /  tim.availableWidth;

          tim.timeExtent = d3.extent(dataset, function(d) {
            return d.t
          });

          if(!tim.timeExtent[0] || !tim.timeExtent[1])
            return;

          // set date from extent
          tim.dateLeft
              .text(tim.timeFormat(new Date(tim.timeExtent[0])));
          tim.dateRight
              .text(tim.timeFormat(new Date(tim.timeExtent[1])));
          
          
          $log.log('::timeline -> draw() w:', tim.availableWidth, ' r:', ratio, scope.filters);
          
          // transform filters in other filters.
          var extension = [
            scope.filters.date__gte? d3.time.format("%Y-%m-%d").parse(scope.filters.date__gte): tim.timeExtent[0],
            scope.filters.date__lte? d3.time.format("%Y-%m-%d").parse(scope.filters.date__lte): tim.timeExtent[1]
          ]

          //
          tim.svg.attr("width", tim.availableWidth)
          tim.fn.x = d3.time.scale()
            .range([0, tim.availableWidth - tim.padding.h * 2]);
          
          tim.fn.x.domain(tim.timeExtent);
          tim.fn.y.domain(d3.extent(dataset, function(d) {return d.weight}));
          
          tim.brush.x(tim.fn.x).extent(tim.timeExtent);
          
          tim.extent(extension)
          tim.stream
            .attr("d", tim.area(dataset));
        };
        
        
        // on graph change, change the timeline as well
        scope.$watch('values', function (timeline) {
          if(!timeline)
            return;
          $log.log('::timeline n. nodes ', timeline.length);
          
          tim.init();
          tim.draw();
          // computate min and max
          
        });
        

        scope.$on(API_PARAMS_CHANGED, function (e) {
          $log.log('::timeline filters:', scope.filters)
          if(scope.filters) {
            $log.log('::timeline -~draw()');
            if(tim.evaluate())
              tim.draw();
          }
        })

        angular.element($window).bind('resize', function() {
          clearTimeout(tim.resizeTimer);
          tim.resizeTimer = setTimeout(tim.draw, 200);
        });
        /*

      link: function postLink (scope, element, attrs) {
        $log.info(':: timeline');
        // on resize babe...
        var timeout, // draw() timeout on resize

            padding  = {
              v: 80, // padding for the line of the timeline
              h: 10
            },

            parseDate = d3.time.format("%Y-%m-%d").parse, // date parser function 

            viewer = d3.select('.viewer'),

            brush  = d3.svg.brush(), 

            svg = viewer
              .append("svg")
              .attr("height", 500),

            context = svg.append("g")
              .attr("class", "context")
              .attr("transform", "translate(" + padding.v + "," + padding.h + ")"),
            // draw main line
            axis = svg.append('path').attr({
              'fill': 'none',
              'stroke': '#b5b5b5',
              'stroke-width': 1
            });



        
        var lies = context
          .append("g")
            .attr("class", "values")

        context.append("g")
          .attr("class", "x brush")
          .call(brush)
            .selectAll("rect")
              .attr("y", 0)
              .attr("height", 30);

        brush.on("brush", function() {
          console.log("brushing babe", brush.extent())
        });

        var leftDate = svg.append('text')
              .attr({'class': 'label'}),
            rightDate = svg.append('text')
              .attr({'class': 'label'});

        var draw = function() {
          clearTimeout(timeout);
          if(!scope.values)
            return;
          var availableWidth = viewer[0][0].clientWidth,
              height = 30,
              values = scope.values.map(function (d) {
                d.date = parseDate(d.day).getTime();
                return d
              });
          
          svg.attr({
            width: availableWidth
          });

          axis.attr({
            d: ['M', padding.v, 40, 'L', availableWidth - padding.v, 40].join(' ')
          });
          
          leftDate
            .attr({
              'text-anchor': 'end',
              transform: 'translate(' +  (padding.v - 15)+ ',30)'
            })
            .text(values[0].day)
            

          rightDate
            .attr({
              
              transform: 'translate(' + (availableWidth - padding.v + 15) +',30)'
            })
            .text(values[values.length-1].day);
          
          
          var x = d3.time.scale().range([0, availableWidth - padding.v*2]),
              y = d3.scale.linear().range([height, 0]),

              min = 0,
              max_count = d3.max(scope.values, function (d) {
                console.log(d)
                return d.count;
              });

              // area = d3.svg.area()
              //   .interpolate("monotone")
              //   .x(function (d) { 
              //     console.log('data', d.date)
              //     return x(d.date);
              //   })
              //   .y0(height)
              //   .y1(function (d) {
              //     console.log('data', d.count)
              //     return y(d.count);
              //   });

          x.domain(d3.extent(values.map(function (d) {
            return d.date;
          })));

          y.domain([0, d3.max(values.map(function(d) {
            return d.count;
          }))]);

          brush.x(x);

          var selected = lies.selectAll('.value')
            .data(values, function(d) {
              return d.day// key to update
            })

          selected.enter().append('circle')
              .attr("r", 2)
              .attr({
                'class': 'value',
                cx: function (d) {
                  return x(d.date);
                },
                cy: function (d) {
                  return y(d.count);
                },
              });

          selected.attr({
                'class': 'value',
                cx: function (d) {
                  return x(d.date);
                },
                cy: function (d) {
                  return y(d.count);
                },
              });

          

          $log.info(':: timeline', max_count);
        };


        angular.element($window).bind('resize', function() {
          clearTimeout(timeout);
          timeout = setTimeout(draw, 200);
        });

        scope.$watch('values', function(val) {
          if(val)
            draw();
        });
        
        */
      }
    }
  })
