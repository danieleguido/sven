'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # matrix directive. Create a matrix visualisation.
 */
angular.module('sven')
  .directive('stream', function($log, $window, $filter) {
    var Stream = function(options) {
      var s = this;
      // main vars
      s.svg;

      s.height = 500;

      s.timers = {
        resize: 0
      };

      s.spacing = {
        gutter: 80,
        colwidth: 130,
        rowheight: 36,
        lineheight: 26,
        headerheight: 54
      }

      s.click = options.click || function() {
        $log.warning('::stream configure click')
      };

      s.viewer = d3.select('#stream .viewer');
      
      // s.width = s.viewer[0][0].clientWidth;

      s.svg    = s.viewer
                  .append("svg")
                    .attr("height", s.height)
                    .attr("width", s.width);

      s.$viewer = $('#stream .viewer')
        .on('mouseenter', '.row', function(e) {
          var _focus = e.currentTarget.__data__.segment__cluster;
          // $log.log('::stream mouseenter, data-id', e.currentTarget.__data__.segment__cluster, $('[data-g="'+ s.focus + '"]').length);
          if(s.previousfocus && s.previousfocus != s.focus) {
            $('.row[data-g="'+ s.previousfocus + '"]').attr('class', 'row')
            $('.row[data-g="'+ _focus + '"]').attr('class', 'row active')
            $('.lines[data-g="'+ s.previousfocus + '"]').attr('class', 'lines')
            $('.lines[data-g="'+ _focus + '"]').attr('class', 'lines active')
          } else if(!s.previousfocus) { // the same, do nothing
            $('.row[data-g="'+ _focus + '"]').attr('class', 'row active')
            $('.lines[data-g="'+ _focus + '"]').attr('class', 'lines active')
          }
          s.previousfocus = _focus;

        })
        .on('mouseleave', '.row', function(e) {
          $('.row[data-g="'+ s.previousfocus + '"]').attr('class', 'row');
          $('.lines[data-g="'+ s.previousfocus + '"]').attr('class', 'lines')
          s.previousfocus = undefined;
        })
        .on('click', '.row', function(e) {
          $log.log('::stream', e.currentTarget.__data__.segment__cluster);
          s.click({
            concept: e.currentTarget.__data__.segment__cluster
          })
        })
      // add special mask definitions

      // draw or redraw
      s.load = function(values) {
        values.sort(function (a,b) {
          return a.G > b.G
        });
        s.values = values;
        // pivot table in order to match schema for the connecting lines
        s.guidelines = {};

        values.forEach(function (group, i) {
          // console.log(group.G, i);
          group.values.forEach(function (d, j) {
            if(!s.guidelines[d.segment__cluster]) {
              // fill the guidelines for this cluster of -1 values.
              s.guidelines[d.segment__cluster] = []
              for(var k = 0; k < values.length; k++)
                s.guidelines[d.segment__cluster].push(-1);
            }
            // change current group value with the correct index
            s.guidelines[d.segment__cluster][i] = j
            
          });
        });
        
        // resize svg crop rect to match values
        s.svg.attr("height", s.spacing.headerheight + 50 * s.spacing.rowheight)
        s.svg.attr("width", s.spacing.gutter + values.length * (s.spacing.colwidth + s.spacing.gutter))
      }

      s.draw = function() {
        console.log('   ', 'draw', s.width)
        // draw elements playground
        s.drawPlayground();

        //
        s.drawLines()
        s.drawRows();
        s.drawlabels();
      }

      


      s.drawBounds = function() {
        console.log('   ', 'drawBounds', s.width)
        // s.svg.attr('width', s.width);
      }

      s.drawPlayground = function() {
        
        // load cols data
        s.cols = s.svg.selectAll('.col')
            .data(s.values, function (d, i) {
              console.log('key', d.G)
              return d.G; // the group
            })

        s.cols.exit()
          .remove()
        // create columns
        var _cols = s.cols.enter()
          .append("g")
            .attr('class', 'col')
            .attr({
              transform: function (d, i) {
                return 'translate(' + (s.spacing.gutter +(i * (s.spacing.colwidth + s.spacing.gutter))) + ', 0)';    
              }
            })

        s.cols.attr({
              transform: function (d, i) {
                return 'translate(' + (s.spacing.gutter +(i * (s.spacing.colwidth + s.spacing.gutter))) + ', 0)';    
              }
            })

        // setup col background
        _cols.append("rect")
          .attr('class', 'context')
          .attr({
            width: s.spacing.colwidth,
            height: function(d) {
              return d.values.length * s.spacing.rowheight
            }
          })

        // setup columns labels
        _cols.append('text')
          .attr('class', 'col-label')
          .attr('text-anchor', 'middle')
          .attr({
            x: s.spacing.colwidth / 2,
            y: 30
          })  

        // setup rows container and rows.
        _cols.append('g')
          .attr('class', 'rows')
          .attr({
            transform: 'translate(0,' + s.spacing.headerheight + ')'
          });

       
        // s.drawRows();
      }

      s.drawLines = function() {
        // transform guidelines into array!
        var _guidelines = [];
        for(var i in s.guidelines) {
          _guidelines.push({
            segment__cluster: i,
            values: s.guidelines[i]
          });
        }
        
        s.lines = s.svg.selectAll('.lines')
            .data(_guidelines.filter(function (d) {
              return d.values.reduce(function (p, c) {
                return p + (c ==-1? 0: 1);
              }) > 0
            }), function (d) {
              return d.segment__cluster; // the group
            });

        var _lines = s.lines.enter()
          .append('g')
            .attr('class', 'lines')
            .attr('data-g', function (d) {
              return d.segment__cluster
            }); // discontinuous line

        s.lines.attr('data-g', function (d) {
                return d.segment__cluster
              }); 

        s.lines
          .exit()
            .remove()
        
        _lines
          .append('path')
            .attr('class', 'line');

        _lines
          .append('path')
            .attr('class', 'dline')
            

        s.lines.select('.dline')
          .attr({
            d: function(d) {
              var p = [],
                  lastUsefulRowIndex,
                  lastUsefulColIndex;
              for(var i = 0; i < d.values.length; i++){
                var col = i,
                    row = d.values[i];
                if(row != -1) {
                  // first shot, draw lines from the half colum till the end.
                  if(lastUsefulColIndex && lastUsefulColIndex  < col-1) {
                    p.push([
                      "M",
                      s.spacing.gutter + s.spacing.colwidth/2 + (lastUsefulColIndex) * (s.spacing.colwidth + s.spacing.gutter),
                      ',',
                      s.spacing.lineheight + s.spacing.headerheight + lastUsefulRowIndex * s.spacing.rowheight,
                      "L",
                      s.spacing.gutter + s.spacing.colwidth + (lastUsefulColIndex) * (s.spacing.colwidth + s.spacing.gutter),
                      ',',
                      s.spacing.lineheight + s.spacing.headerheight + lastUsefulRowIndex * s.spacing.rowheight,
                      "L",
                      s.spacing.gutter + (col) * (s.spacing.colwidth + s.spacing.gutter),
                      ',',
                      s.spacing.lineheight + s.spacing.headerheight + row * s.spacing.rowheight,
                      "L",
                      s.spacing.gutter +  s.spacing.colwidth/2 + col * (s.spacing.colwidth + s.spacing.gutter),
                      ',',
                      s.spacing.lineheight + s.spacing.headerheight + row * s.spacing.rowheight,
                    ].join(''))
                  }
                  lastUsefulRowIndex = row
                  lastUsefulColIndex = col
                }
              };
              return p.join('');
            }
          })


        s.lines.select('.line')
            .attr({
              d: function(d) {
                var p = [],
                    lastUsefulRowIndex,
                    lastUsefulColIndex;
                for(var i = 0; i < d.values.length; i++){
                  var col = i,
                      row = d.values[i];
                  if(row != -1) {
                    // first shot, draw lines from the half colum till the end.
                    

                    // consequent columns
                    if(lastUsefulColIndex == col-1) {
                      p.push([
                        "M",
                        s.spacing.gutter + s.spacing.colwidth/2 + (lastUsefulColIndex) * (s.spacing.colwidth + s.spacing.gutter),
                        ',',
                        s.spacing.lineheight + s.spacing.headerheight + lastUsefulRowIndex * s.spacing.rowheight,
                        "L",
                        s.spacing.gutter + s.spacing.colwidth + (lastUsefulColIndex) * (s.spacing.colwidth + s.spacing.gutter),
                        ',',
                        s.spacing.lineheight + s.spacing.headerheight + lastUsefulRowIndex * s.spacing.rowheight,
                        "L",
                        s.spacing.gutter + (col) * (s.spacing.colwidth + s.spacing.gutter),
                        ',',
                        s.spacing.lineheight + s.spacing.headerheight + row * s.spacing.rowheight,
                        "L",
                        s.spacing.gutter +  s.spacing.colwidth/2 + col * (s.spacing.colwidth + s.spacing.gutter),
                        ',',
                        s.spacing.lineheight + s.spacing.headerheight + row * s.spacing.rowheight,
                      ].join(''))
                    }
                    lastUsefulRowIndex = row
                    lastUsefulColIndex = col
                  }

                  // if(row == -1) {
                  //   // if(lastUsefulRowIndex)
                  //   //   p.push("M" + (i*100) + "," +  )
                  //   // skip this step
                  // } else {
                  //   i
                  //   p.push(d.values[i] == -1?)
                  //   lastUsefulRowIndex = rowIndex;
                  // }

                }
                return p.join(''); 
              },
            });
      }

      s.drawlabels = function() {

        s.cols.selectAll('text.col-label')
          .text(function (d) {
            return d3.time.format("%B %d, %Y")(d3.time.format("%Y-%m-%d").parse(d.G))
          });

        s.rows.selectAll('text.row-label')
          .text(function (d) {
            return $filter('truncate')(d.contents.split('||')[0], 25)
          });
      }

      s.drawRows = function() {
        s.rows = s.cols.select('.rows').selectAll('.row')
          .data(function (d) {
            return d.values
          });

        // create row
        var _rows = s.rows.enter()
          .append("g")
            .attr('class', 'row')
            .attr('data-g', function (d) {
              return d.segment__cluster
            })
            .attr({
              transform: function (d, i) {
                return 'translate(0, ' + (i * (s.spacing.rowheight)) + ')';    
              }
            })

        _rows.append('text')
          .attr('class', 'row-label')
          .attr({
            'text-anchor': 'middle',
            x: s.spacing.colwidth / 2,
            y: 20
          })  
      }

      // resize
      s.resize = function() {
        console.log('   ', 'resize')
        clearTimeout(s.timers.resize);
        s.timers.resize = setTimeout(function() {
          // s.width = s.viewer[0][0].clientWidth;
          // s.draw();
        }, 200);
      }
    };


    return {
      template: '<div class="mouse tooltip">...</div><div class="viewer"></div>',
      restrict: 'E',
      scope: {
        values: '=',
        click: '&'
      },
      link: function postLink (scope, element, attrs) {
        $log.log('::stream init with values', scope.values.length);

        var s = new Stream({
          click: scope.click
        });


        scope.$watch('values', function (values) {
          if(!values)
            return;
          $log.log('::stream n. nodes ', values.length);
          s.load(values);
          // computate min and max
          s.draw()
        });

        // listener on resize
        angular.element($window).bind('resize', s.resize);
      }
    }
  });