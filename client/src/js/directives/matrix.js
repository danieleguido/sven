'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # matrix directive. Create a matrix visualisation.
 */
angular.module('sven')
  .directive('matrix', function() {
    return {
      template: '<div class="mouse tooltip">...</div><div class="viewer"></div>',
      restrict: 'EA',
      scope: {
        data: '=',
        measure: '=',
        groups: '=',
        bounds: '=',
        toggle: '&'
      },
      link: function postLink (scope, element, attrs) {
        var minRadius  = 1,
            maxRadius  = 10,
            colspacing = maxRadius * 4,
            lineHeight = 28,
            marginTop = 160,
            marginLeft = 200; // labels excluded.



        var svg = d3.select('.viewer')
          .append("svg")
          .attr("height", 500)
          .attr("width", 500);

        // create labels
        // appending labels
        svg
          .append("text")
          .text('concept example')
          .attr({
            x: 40,
            y: 100,
            'class': 'header'
          })

        svg
          .append("text")
          .text('tf')
          .attr({
            transform: 'translate(' + marginLeft + ', 100)',
            'class': 'header'
          })

        svg
          .append("text")
           .text('tfidf')
          .attr({
            transform: 'translate(' + (marginLeft + colspacing) + ', 100)',
            'class': 'header'
          })

        /**
          
        */
        var draw = function(data) {
          //
          console.log('draw()', scope.bounds);

          var tfRadius = d3.scale.sqrt()
            .range([
              minRadius, maxRadius
            ]).domain([
              scope.bounds.min_tf,
              scope.bounds.max_tf
            ]);

          var tfidfRadius = d3.scale.sqrt()
            .range([
              8, 9
            ]).domain([
              scope.bounds.min_tfidf,
              scope.bounds.max_tfidf
            ]);

          // move by Y
          var transformationMatrix = function(d,i) {
            return 'matrix(' + [1, 0, 0, 1, 0, i*lineHeight + marginTop].join(' ') + ')';
          }

          // move by X, group aware
          var transformationColMatrix = function(d,i) {
            return 'translate(' + (i*colspacing) + ', 0)';
          }


          // create (or update) rows
          var rows = svg.selectAll('.block')
            .data(data, function(d, i) {
              return i;//d.segment__cluster; // a.k.a. something
            })

          var blocks = rows.enter()
            .append('g')
              .attr('class', function(d) {
                return 'block ' + (d.status || '');
              })
              .attr('transform', transformationMatrix)
          
          blocks
            .append('text')
              .attr({
                x: 40,
                y: - 12
              })
          
          blocks
            .append('circle')
              .attr({
                class: 'global tf',
                cx: marginLeft,
                cy: - lineHeight/2,
                r: function (d) { return tfRadius(d.tf) }
              })

          blocks
            .append('circle')
              .attr({
                class: 'global tfidf',
                cx: marginLeft + maxRadius,
                cy: - lineHeight/2,
                r: function (d) { return tfidfRadius(d.tfidf) }
              })


          rows
            .exit()
              .remove()

          rows
            .select('text')
              .text(function(d) {
                  return d.segment__cluster || '...'
                });

          rows
            .select('circle.tf.global')
              .transition()
                .attr({
                  r: function (d) { return tfRadius(d.tf) }
                })

          rows
            .select('circle.tfidf.global')
              .transition()
                .attr({
                  r: function (d) { return tfidfRadius(d.tfidf) }
                })

          rows
            .transition()
            .attr('transform', transformationMatrix)
          
          // 
          // Position groups 
          //
          var cols = rows
            .selectAll('.measure')
              .data(function(d) {
                return scope.groups.map(function(g) {
                  var _g = {
                    slug:  g.slug,
                    name:  g.name,
                    id:    g.id,
                    t:     g.distribution,
                    d:     0, // distribution for the
                    tf:    0.0,
                    tfidf: 0.0,
                  };
                  
                  if(!d.cols)
                    return _g; // otherwise enrich

                  for(var i=0; i<d.cols.length; i++) {
                    if(d.cols[i].G == g.name) {
                      _g.tf    = d.cols[i].tf;
                      _g.tfidf = d.cols[i].tfidf;
                      _g.d     = d.cols[i].distribution
                      break;
                    }
                  }

                  return _g;
                });
              });

          var measures = cols.enter()
            .append('g')
              .attr('class', function(d) {
                return 'measure';
              })
              .attr('transform', transformationColMatrix)

          measures
            .append('circle')
              .attr({
                class: 'tf',
                cx: marginLeft + colspacing,
                cy: - lineHeight/2,
                r: function (d) { return tfRadius(d.tf) }
              })
          measures
            .append('circle')
              .attr({
                class: 'tfidf',
                cx: marginLeft + colspacing + maxRadius,
                cy: - lineHeight/2,
                r: function (d) { return tfRadius(d.tfidf) }
              })
          cols.exit().remove();
          cols
            .select('circle.tf')
              .transition()
                .attr({
                  r: function (d) { return tfRadius(d.tf) }
                })

          cols
            .select('circle.tfidf')
              .transition()
                .attr({
                  r: function (d) { return tfidfRadius(d.tfidf) }
                })





        };

        scope.$watch('data', function (current, previous) {
          if(current)
            draw(current);
        });
      }
    }
  })