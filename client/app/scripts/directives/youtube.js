'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:youtube
 * @description
 * # youtube
 */
angular.module('svenClientApp')
  .directive('youtube', function () {
    return {
      template: '<div></div>',
      restrict: 'E',
      scope:{
        url:'=',
        height: '='
      },
      link: function postLink(scope, element, attrs) {
        var videoid = scope.url.match(/v=([\w]+)/).pop();

        element.html('<iframe width="100%" height="' + scope.height + '" src="http://www.youtube.com/embed/' + videoid + '?feature=oembed" frameborder="0" allowfullscreen></iframe>');
      }
    };
  });