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
        onbrush: '&'
      },
      template: '<div class="brushdate left "></div><div class="brushdate right "></div><div class="date left "></div><div class="date right "></div><div class="mouse tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div><div class="viewer"></div>',
      link : function(scope, element, attrs) {
        
        var δ = { css:{}, ƒ:{}};
        
        δ.padding = {
          v: 10,
          h: 10  
        };
        
        δ.dimensions = {
          w: 1000,
          h: 50  
        };
        
        δ.ƒ.x = d3.time.scale()
            .range([δ.padding.h * 2, δ.dimensions.w - δ.padding.h * 2]);
        δ.ƒ.x.domain([0, 100]);
        δ.ƒ.y = d3.scale.sqrt()
            .range([30, 0]);
        


        δ.init = function() {
          δ.viewer      = d3.select('#timeline .viewer');
          δ.tooltip     = d3.select('#timeline .tooltip');
          δ.tooltipText = d3.select('#timeline .tooltip-inner');
          δ.dateLeft    = d3.select('#timeline .date.left');
          δ.dateRight   = d3.select('#timeline .date.right');
          δ.brushDateLeft    = d3.select('#timeline .brushdate.left');
          δ.brushDateRight   = d3.select('#timeline .brushdate.right');
              
          δ.brush       = d3.svg.brush().x(δ.ƒ.x);
          
          δ.svg     = δ.viewer
            .append("svg")
              .attr("height", δ.dimensions.h)
              .attr("width", δ.dimensions.w);
          
          δ.stream  = δ.svg.append("path")
            .attr("transform", "translate("+ δ.padding.v +"," + δ.padding.h + ")")
            .attr("class", "stream")
          
          δ.pointer = δ.svg.append("rect")
            .attr({
              height: δ.dimensions.h,
              width: 1,
              fill: 'magenta'
            })
            .style({
              'opacity': 0
            })
            
          δ.context = δ.svg.append("g")
              .attr("class", "context")
              .attr("transform", "translate(" + δ.padding.v + "," + δ.padding.h/2 + ")"),                
          
          δ.gBrush = δ.context.append("g")
              .attr("class", "x brush")
              .call(δ.brush);

           δ.gBrush.selectAll("rect")
                  .attr({
                    y: 0,
                    height: δ.dimensions.h - δ.padding.h
                  });

          
          δ.area = d3.svg.area()
              //.interpolate("monotone")
              .x(function (d) {
                return δ.ƒ.x(d.t);
              })
              .y0(function (d) {
                return δ.ƒ.y(d.weight);
              })
              .y1(30);
          
          δ.brush.on("brush", function() {
            return; 
            
            var extent = δ.brush.extent();
            console.log(extent[0], extent[1])
            if(!extent[0] || !extent[1])
              return;
            // commento
            // console.log('::timeline @brush', new Date(extent[0]))
             // d3.time.format("%B %d, %Y")(extent[0]))
            if(typeof extent[0] == 'object') {
              δ.brushDateLeft.style({
                left: δ.ƒ.x(extent[0]) + 50
              }).text(d3.time.format("%B %d, %Y")(extent[0]));
              δ.brushDateRight.style({
                left: δ.ƒ.x(extent[1]) + 110 + 50
              }).text(d3.time.format("%B %d, %Y")(extent[1]));
            }

            clearTimeout(δ.brushTimer);
            δ.brushTimer = setTimeout(function(){
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
            
            //console.log("brushing babe", δ.brush.extent())
          });
          
          δ.svg.on("mouseover", function(){
            δ.tooltip.style({'opacity': 1});
            δ.pointer.style({'opacity': 1})
          });
          
          δ.svg.on("mouseout", function(){
            δ.tooltip.style({'opacity': 0});
            δ.pointer.style({'opacity': 0})
          });
          

          δ.timeFormat = d3.time.format("%B %d, %Y");
          
          δ.svg.on("mousemove", function(){
            var pos = d3.mouse(this),
                date = new Date(δ.ƒ.x.invert(pos[0]-δ.padding.v));
            
            δ.pointer.style({
              'opacity': pos[0] < δ.padding.v || pos[0] > δ.availableWidth - δ.padding.v? 0:1
            }).attr('x', pos[0])
            δ.tooltip.style({
              'left': pos[0] + 150 + 'px',
              'opacity': pos[0] < δ.padding.v || pos[0] > δ.availableWidth - δ.padding.v? 0:1
            })
            δ.tooltipText.text(
              δ.timeFormat(date)
            );
            
              
          })
          
           δ.availableWidth = δ.viewer[0][0].clientWidth;
          $log.log('::timeline -> init() ');
        };
        
        
        δ.extent = function(extension) {
          
          if(!extension[0] || !extension[1])
            return;
          δ.gBrush.call(δ.brush.extent(extension));
          δ.gBrush.call(δ.brush.event);
        }
        
        δ.draw = function() {
          clearTimeout(δ.resizeTimer);
          if(!δ.viewer)
            return;

          δ.availableWidth = δ.viewer[0][0].clientWidth;
          var parseDate = d3.time.format("%Y-%m-%d").parse;
          var dataset = angular.copy(scope.values).map(function (d) {
                d.t = parseDate(d.day).getTime();
                d.weight = d.count;
                return d;
              }).sort(function (a, b) {
                return a.t < b.t ? -1 : 1
              }),
              ratio = dataset.length /  δ.availableWidth,
              timeExtent = d3.extent(dataset, function(d) {return d.t});
          if(!timeExtent[0] || !timeExtent[1])
            return;
          // set date from extent
          δ.dateLeft
              .text(δ.timeFormat(new Date(timeExtent[0])));
          δ.dateRight
              .text(δ.timeFormat(new Date(timeExtent[1])));
          
          
          $log.log('::timeline -> draw() w:', δ.availableWidth, ' r:', ratio, scope.filters);
          
          // transform filters in other filters.
          var extension = [
            scope.filters.date__gte? d3.time.format("%Y-%m-%d").parse(scope.filters.date__gte): timeExtent[0],
            scope.filters.date__lte? d3.time.format("%Y-%m-%d").parse(scope.filters.date__lte): timeExtent[1]
          ]

          //
          δ.svg.attr("width", δ.availableWidth)
          δ.ƒ.x = d3.time.scale()
            .range([0, δ.availableWidth - δ.padding.h * 2]);
          
          δ.ƒ.x.domain(timeExtent);
          δ.ƒ.y.domain(d3.extent(dataset, function(d) {return d.weight}));
          
          δ.brush.x(δ.ƒ.x).extent(timeExtent);
          
          δ.extent(extension)
          δ.stream
            .attr("d", δ.area(dataset));
        };
        
        
        // on graph change, change the timeline as well
        scope.$watch('values', function (timeline) {
          if(!timeline)
            return;
          $log.log('::timeline n. nodes ', timeline.length);
          
          δ.init();
          δ.draw();
          // computate min and max
          
        });
        

        scope.$on(API_PARAMS_CHANGED, function (e) {
          $log.log('::timeline filters:', scope.filters)
          if(scope.filters) {
            $log.log('::timeline -~draw()');
            δ.draw();
          }
        })

        angular.element($window).bind('resize', function() {
          clearTimeout(δ.resizeTimer);
          δ.resizeTimer = setTimeout(δ.draw, 200);
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
